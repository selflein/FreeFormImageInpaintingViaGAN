import os
import argparse
from pathlib import Path

import cv2 as cv
import numpy as np
from scipy import io
import matplotlib.pyplot as plt

# Based on
# https://github.com/opencv/opencv/blob/master/samples/dnn/edge_detection.py

parser = argparse.ArgumentParser(description='Generates edge masks for input '
                                             'images.')
parser.add_argument('--input', help='Path to image folder.')
parser.add_argument('--output', help='Path to output image folder.')
parser.add_argument('--prototxt', help='Path to deploy.prototxt', required=True)
parser.add_argument('--caffemodel',
                    help='Path to hed_pretrained_bsds.caffemodel',
                    required=True)
parser.add_argument('--visualize', type=bool, default=False)


class CropLayer(object):
    def __init__(self, params, blobs):
        self.xstart = 0
        self.xend = 0
        self.ystart = 0
        self.yend = 0

    # Our layer receives two inputs. We need to crop the first input blob to
    # match a shape of the second one (keeping batch size and number of
    # channels)
    def getMemoryShapes(self, inputs):
        inputShape, targetShape = inputs[0], inputs[1]
        batchSize, numChannels = inputShape[0], inputShape[1]
        height, width = targetShape[2], targetShape[3]

        self.ystart = (inputShape[2] - targetShape[2]) // 2
        self.xstart = (inputShape[3] - targetShape[3]) // 2
        self.yend = self.ystart + height
        self.xend = self.xstart + width

        return [[batchSize, numChannels, height, width]]

    def forward(self, inputs):
        return [inputs[0][:, :, self.ystart:self.yend, self.xstart:self.xend]]


if __name__ == '__main__':
    args = parser.parse_args()
    cv.dnn_registerLayer('Crop', CropLayer)

    # Load the model.
    net = cv.dnn.readNetFromCaffe(args.prototxt, args.caffemodel)
    for img_path in Path(args.input).iterdir():
        frame = cv.imread(str(img_path))

        height, width, _ = frame.shape

        inp = cv.dnn.blobFromImage(frame, scalefactor=1.0,
                                   size=(width, height),
                                   mean=(
                                       104.00698793, 116.66876762,
                                       122.67891434),
                                   swapRB=False, crop=False)
        net.setInput(inp)

        out = net.forward()
        hed = cv.resize(out[0, 0], (width, height))
        hed = (hed > .6).astype(np.int8) * 255
        # kernel = np.ones((3, 3), np.uint8)
        # img_erosion = cv.erode(hed, kernel, iterations=1)

        if args.visualize:
            fig, ax = plt.subplots(3, 1)
            ax[0].imshow(frame)
            ax[1].imshow(hed)
            # ax[2].imshow(img_erosion)
            plt.show()

        cv.imwrite(os.path.join(args.output, img_path.name), hed)
