# Copyright (c) 2019 Graphcore Ltd. All rights reserved.
import numpy as np
import popart
import time
from torchvision import datasets, transforms
import dataloader
import onnx
import torch
from absl import app, flags
from data import DataSet

def load_dataset(tensors):
    transform = transforms.Compose(
            [transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.ConvertImageDtype(torch.float16),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]),
        ])
    dataset = datasets.ImageFolder(
        root=FLAGS.data_dir,
        transform=transform)

    tensor_type = 'float16'

    loader = dataloader.DataLoader(
        dataset,
        batch_size=FLAGS.micro_batch_size*FLAGS.device_iterations,
        tensor_type=tensor_type,
        shuffle=False,
        num_workers=FLAGS.num_workers,
        
        drop_last=True)  # In the case there is not sufficient data in last batch drop it

    return DataSet(
        tensors,
        FLAGS.micro_batch_size,
        FLAGS.device_iterations,
        loader)


def graph_builder():
    model_path = (
        "models" if not FLAGS.model_path else FLAGS.model_path
    )
    proto = f"{model_path}/{FLAGS.model_name}/model_{FLAGS.micro_batch_size}.onnx"

    builder = popart.Builder(
        proto, opsets={"ai.onnx": 10, "ai.onnx.ml": 1, "ai.graphcore": 1})
    input_id = builder.getInputTensorIds()[0]

    if FLAGS.synthetic:

        input_shape = [int(FLAGS.micro_batch_size), 3, 224, 224]
        data = {
            input_id: np.random.normal(0, 1, input_shape).astype(np.float16)
        }

        if FLAGS.device_iterations > 1:
            data = {k: np.repeat(v[np.newaxis], FLAGS.device_iterations, 0)
                    for k, v in data.items()}

    else:
        data = load_dataset([input_id])
    output_id = builder.getOutputTensorIds()[0]
    output = {output_id: popart.AnchorReturnType("ALL")}

    list_of_convolution_ids = []
    graph_proto = onnx.load(proto).graph
    # get list of all IDs of outputs of convolutions. We need these so we can adjust their memory proportions from the default
    for i in range(len(graph_proto.node)):
        if graph_proto.node[i].op_type == 'Conv':
            list_of_convolution_ids.append(graph_proto.node[i].output[0])
    memoryProportion = 0.3
    if FLAGS.batch_size == 5:
        memoryProportion = 0.26
    for id in list_of_convolution_ids:
        builder.setAvailableMemoryProportion(id, memoryProportion)
    proto = builder.getModelProto()
    graph_transformer = popart.GraphTransformer(proto)
    graph_transformer.convertFloatsToHalfs()
    return graph_transformer.getModelProto(), data, output, output_id


def main(argv):
    FLAGS = flags.FLAGS
    print(f"micro batch size is {FLAGS.micro_batch_size}")
    print(f"batch size is {FLAGS.batch_size}")
    print(f"device_iterations is {FLAGS.device_iterations}")
    proto, data, outputs, output_id = graph_builder()
    print(f"Model: {FLAGS.model_name}")
    if not FLAGS.synthetic:
        print(f"Data_dir: {FLAGS.data_dir}")
    else:
        print(f"Using synthetic data")
    print(f"Data_sub_dir for this process: {FLAGS.data_sub_dir}")
    print(f"num_workers: {FLAGS.num_workers}")
    print(f"device iterations: {FLAGS.device_iterations}")
    dataFlow = popart.DataFlow(FLAGS.device_iterations, outputs)
    
    # Create a session to compile and execute the graph
    options = popart.SessionOptions()
    if FLAGS.synthetic:
        options.syntheticDataMode = popart.SyntheticDataMode.Zeros
    options.instrumentWithHardwareCycleCounter = FLAGS.report_hw_cycle_count

    # Configure precision of convolutions and MatMuls
    if FLAGS.half_partials:
        options.convolutionOptions = {'partialsType': 'half'}
        options.partialsTypeMatMuls = "half"

    # Select a device
    deviceManager = popart.DeviceManager()
    device = deviceManager.acquireAvailableDevice(1)
    print(f"{device}\n")

    session = popart.InferenceSession(
        fnModel=proto,
        deviceInfo=device,
        dataFlow=dataFlow,
        userOptions=options)

    print("Compiling...")
    startCompilation = time.time()
    session.prepareDevice()
    print(f"Time to compile: {time.time() - startCompilation}")

    # Create buffers to receive results from the execution
    anchors = session.initAnchorArrays()
    # Copy weights and optimisation parameters onto the device
    session.weightsFromHost()

    def report_time(duration, data_duration=None, compute_duration=None):
        report_string = "Total {:<8.3} sec.".format(duration)
        if data_duration:
            report_string += "   Preprocessing {:<8.3} sec ({:4.3}%).".format(
                data_duration, 100 * (data_duration/duration))
        if compute_duration:
            report_string += "   Compute {:<8.3} sec ({:4.3}%).".format(
                compute_duration, 100 * (compute_duration/duration))
        report_string += "   {:5f} images/sec.".format(
            int(FLAGS.micro_batch_size * FLAGS.device_iterations / duration))
        print(report_string)
        if FLAGS.report_hw_cycle_count:
            print("Hardware cycle count per 'run':", session.getCycleCount())

    print("Executing...")

    # Run
    start = time.time()
    durations = []
    if FLAGS.synthetic:
        for i in range(FLAGS.iterations):
            stepio = popart.PyStepIO(data, anchors)
            data_time = time.time()
            data_d = data_time - start
            # Run compute
            session.run(stepio)
            # Calc compute duration
            results = anchors[output_id]
            comp_d = time.time() - data_time
            # Calc total duration
            t = time.time() - start
            report_time(t, data_d, comp_d)
            durations.append(t)
            start = time.time()
        duration = np.mean(durations)
    else:
        for d in data:
            stepio = popart.PyStepIO(d, anchors)
            # Calc data duration
            data_time = time.time()
            data_d = data_time - start
            # Run compute
            session.run(stepio)
            # Calc compute duration
            results = anchors[output_id]
            comp_d = time.time() - data_time
            # Calc total duration
            t = time.time() - start
            report_time(t, data_d, comp_d)
            durations.append(t)
            start = time.time()
        duration = np.mean(durations)


FLAGS = flags.FLAGS
flags.DEFINE_integer("micro_batch_size", 64, "Batch size per device")
flags.DEFINE_integer("batch_size", 256, "Overall size of batch (across all devices).")
flags.DEFINE_integer(
    "num_ipus", 8, "Number of IPUs to be used. One IPU runs one compute process.")
flags.DEFINE_string("data_sub_dir", "datasets/",
                    "Child directory containing one subdirectory dataset")
flags.DEFINE_integer("num_workers", 2, "Number of threads per dataloader")
flags.DEFINE_integer("device_iterations", 200,
                     "Number of batches of images to fetch on the host ready for streaming onto the device, reducing host IO")
flags.DEFINE_string("data_dir", "datasets/",
                    "Parent directory containing subdirectory dataset(s). Number of subdirs should equal num_ipus")
flags.DEFINE_string("model_name", "resnext101_32x4d",
                    "model name. Used to locate ONNX protobuf in models/")
flags.DEFINE_bool("synthetic", False, "Use synthetic data created on the IPU for inference")
flags.DEFINE_integer(
    "iterations", 1, "Number of iterations to run if using synthetic data. Each iteration uses one `device_iterations` x `batch_size` x `H` x `W` x `C` sized input tensor")
flags.DEFINE_bool(
    "report_hw_cycle_count",
    False,
    "Report the number of cycles a 'run' takes."
)
flags.DEFINE_string(
    "model_path", None,
    (
        "If set, the model will be saved to this"
        " specfic path, instead of models/"
    )
)
flags.DEFINE_string(
    "log_path", None,
    (
        "If set, the logs will be saved to this"
        " specfic path, instead of logs/"
    )
)
flags.DEFINE_bool(
    "hide_output", True,
    (
        "If set to true the subprocess that the model"
        " is run with will hide output."
    )
)
flags.DEFINE_bool(
    "half_partials", True,
    (
        "If set, the model will use half-precision (fp16) partials"
        " in the convolution and MatMul operations."
    )
)

if __name__ == '__main__':
    app.run(main)
