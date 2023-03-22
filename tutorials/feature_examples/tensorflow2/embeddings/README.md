<!-- Copyright (c) 2020 Graphcore Ltd. All rights reserved. -->
# TensorFlow 2 Embeddings Example

These examples train an IPU model with an embedding layer and an
LSTM to predict the sentiment of an IMDB review.

There are variants covering the use of `keras.Model` and `keras.Sequential`
for single IPU execution. Additionally, there are 2 IPU variants showing how to
use pipelining with either a `keras.Model` or a `keras.Sequential` model on the IPU.

These examples were derived from this Keras example:
<https://github.com/keras-team/keras/blob/1a3ee8441933fc007be6b2beb47af67998d50737/examples/imdb_lstm.py>

## File structure

* `imdb.py` Python script to train the 2-IPU pipelined model.
* `imdb_sequential.py` Python script to train the 2-IPU pipelined sequential model.
* `imdb_single_ipy.py` Python script to train the single-IPU model.
* `imdb_single_ipu_sequential.py` Python script to train the single-IPU sequential model.
* `README.md` This file.
* `requirements.txt` Required packages for the tests
* `test_imdb.py` Integration tests

## How to use this example

1) Prepare the TensorFlow environment.

   Install the Poplar SDK (see the [Getting Started](https://docs.graphcore.ai/en/latest/getting-started.html) guide for your IPU system). Make sure to run the enable.sh script for Poplar and activate a Python 3 virtualenv with the tensorflow-2 and ipu_addons_tensorflow2 wheels from the Poplar SDK installed.

2) Train the graph.

    `python3 imdb.py`

   Or a variant as above.

## Extra information

### Model

The model contains an embedding layer with a 20k dictionary, an LSTM layer, and
a projection down to a binary sentiment.

#### Options

There are no options for these scripts.

## Tests

To run the tests:

`python3 -m pip install -r requirements.txt`

`python3 -m pytest`

### License

This example is licensed under the MIT license - see the LICENSE file at the top level of this repository.

It includes derived work from:

Keras, <https://github.com/keras-team/keras/tree/1a3ee8441933fc007be6b2beb47af67998d50737>
(Source file has been deleted from the master branch)

All contributions by François Chollet:
Copyright (c) 2015 - 2019, François Chollet.
All rights reserved.

All contributions by Google:
Copyright (c) 2015 - 2019, Google, Inc.
All rights reserved.

All contributions by Microsoft:
Copyright (c) 2017 - 2019, Microsoft, Inc.
All rights reserved.

All other contributions:
Copyright (c) 2015 - 2019, the respective contributors.
All rights reserved.

Each contributor holds copyright over their respective contributions.
The project versioning (Git) records all such contribution source information.

The MIT License (MIT)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
