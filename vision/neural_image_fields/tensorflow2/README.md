# Neural Image Fields
Neural image fields

| Framework | domain | Model | Datasets | Tasks| Training| Inference | Reference |
|-------------|-|------|-------|-------|-------|---|---|
| TensorFlow2 | Vision | Neural Image Fields | Images (see below) |  | ✅ | ✅ | [NERF](https://arxiv.org/abs/2003.08934), [Fourier Features Let Networks Learn High Frequency Functions in Low Dimensional Domains](https://arxiv.org/abs/2006.10739) |


## Instructions summary

1. Install and enable the Poplar SDK (see Poplar SDK setup)

2. Install the system and Python requirements (see Environment setup)

3. Download the ISBI Challenge 2012 dataset (See Dataset setup)


## Poplar SDK setup
To check if your Poplar SDK has already been enabled, run:
```bash
 echo $POPLAR_SDK_ENABLED
 ```

If no path is provided, then follow these steps:
1. Navigate to your Poplar SDK root directory

2. Enable the Poplar SDK with:
```bash 
cd poplar-<OS version>-<SDK version>-<hash>
. enable.sh
```

3. Additionally, enable PopArt with:
```bash 
cd popart-<OS version>-<SDK version>-<hash>
. enable.sh
```

More detailed instructions on setting up your environment are available in the [poplar quick start guide](https://docs.graphcore.ai/projects/graphcloud-poplar-quick-start/en/latest/).


## Environment setup
To prepare your environment, follow these steps:

1. Create and activate a Python3 virtual environment:
```bash
python3 -m venv <venv name>
source <venv path>/bin/activate
```

2. Navigate to the Poplar SDK root directory

3. Install the Tensorflow2 and IPU Tensorflow add-ons wheels:
```bash
cd <poplar sdk root dir>
pip3 install tensorflow-2.X.X...<OS_arch>...x86_64.whl
pip3 install ipu_tensorflow_addons-2.X.X...any.whl
```
For the CPU architecture you are running on

4. Navigate to this example's root directory

5. Install the apt requirements:
```bash
sudo apt install $(<required_apt_packages.txt)
```

5. Install the Python requirements:
```bash
pip3 install -r requirements.txt
```

## Running this example
Train a neural radiance field from the provided example image, then reconstruct the image from the trained function approximator:

```bash
python3 train_nif.py --train-samples 1000000 --input Mandrill_portrait_2_Berlin_Zoo.jpg --disable-psnr
python3 predict_nif.py --output reconstruction.png --original Mandrill_portrait_2_Berlin_Zoo.jpg
```

This first command will train a neural representation of the input image and save a keras model to a default path.
The second command loads the saved model and uses it to generate a reconstructed image which is saved to the
specified output file. It also loads the original image to compute the peak signal to noise ratio (PSNR) of the
reconstruction. For a higher quality approximation try increasing `--train-samples` and `--epochs`. You can also
launch Tensorboard which will monitor the reconstructed image during training:
```bash
tensorboard --logdir ./logs
```


##  Custom training/inference and other features

### Graphcore: Neural Image Fields
Neural image fields are a simplified version of neural radiance fields: [NERF](https://arxiv.org/abs/2003.08934).
In NERF a 3D volumetric is learned as a function of ray position (x, y, z) and direction (phi, psi) whereas a NIF
instead learns a 2D image as a function of pixel (u, v) coordinates. I.e. in NERF a neural network is trained as
a function approximator to learn a (relatively) low dimensaional function (x, y, z, phi, psi) -> (r, g, b, w).
In this example we instead learn an even lower dimensional function (u, v) -> (r, g, b) where (u,v) are input
image coordinates and the output is the red, green, blue colour value at that (sub-)pixel coordinate: a trained NIF can
therefore be used to reconstruct point samples from the original image. Although the function is simpler, the
neural network architecture (MLP/relu-networks) and the embedding of low dimensional input co-ordinates into a
higher dimensional "position encoding" (using fourier features) is almost identical in both cases. With careful
selection of hyper-parameters it is possible to use this as a form of neural image compression.

The model architecture in this example is a mixture of the principles from the NERF paper
and those described in [Fourier Features Let Networks Learn High Frequency Functions in Low Dimensional Domains](https://arxiv.org/abs/2006.10739)
but note that it is a different model from the one in the paper. For example this model supports
HDR images which the original does not due to its final sigmoid layer. There is also an option to
create a SIREN network architecture, again, that model is not identical to the one in the paper:
[Implicit Neural Representations with Periodic Activation Functions](https://arxiv.org/abs/2006.09661).

This example consists of a TF2/Keras script to train a NIF representation of a single input image and a second script
to reconstruct an image from the trained network. It also demonstrates the following IPU Keras specific features:
- Automatic data parallelism (instructions below).
- How to train with fp16 master weights and how to enable/disable stochastic rounding.
- How to run evaluation in a separate process, on a second IPU, invoked from a custom Keras callback.
- How to support IPU/GPU/CPU in the same program with minimal changes in training scripts.

### PSNR evaluation

There is a custom keras callback for launching a separate evaluation process so as not to interrupt training.
This process loads the saved model from the previous epoch and computes the peak-signal-to-noise-ratio of the
reconstructed image versus the original. (Note that the example command above disables evaluation because the
epochs are so short that the single evaluation process can not keep up with training). On a longer traning run
the evaluation frequency can be configured to ensure each process finishes before the next epoch is complete by
choosing the `--callback-period` appropriately.

### Data Parallel Training

The program can also utilise 
[IPU Keras automatic data-parallelism](https://docs.graphcore.ai/projects/tensorflow-user-guide/en/latest/tensorflow/keras_tf2.html#automatic-data-parallelism)
by setting `--replicas` to the number of IPUs you wish to use. Be sure to increase `--gradient-accumulation-count` accordingly (larger counts reduce the
frequency of inter-IPU reduction of gradients to improve throughput).

## Example Image

The example image was chosen due to its combination of high and low frequency components to better illustrate the limits of the neural representation. The example image
`Mandrill_portrait_2_Berlin_Zoo.jpg` is free to use under the [Creative Commons Attribution 2.0 generic](https://creativecommons.org/licenses/by/2.0/deed.en)
license: it was originally posted to [Flickr by wwarby](https://flickr.com/photos/26782864@N00/47036477821) and
was available under the cc-by-2 license on 21st December 2021.

![Source](https://upload.wikimedia.org/wikipedia/commons/b/be/Mandrill_portrait_%282%29%2C_Berlin_Zoo.jpg).
