#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cv2 as cv
import numpy as np
from scipy.misc import imrotate
from scipy.ndimage.interpolation import shift
from sklearn.preprocessing import scale


class Transform(object):

    def __init__(self, **params):
        [setattr(self, key, value) for key, value in params.iteritems()]

    def transform(self, datum, datadir, train=True):
        img_fn = '%s/images/%s' % (datadir, datum[0])
        self._img = cv.imread(img_fn)
        self.orig = self._img.copy()
        self._joints = np.asarray([int(float(p)) for p in datum[1:]])

        if hasattr(self, 'padding'):
            self.crop()
        if hasattr(self, 'flip'):
            self.fliplr()
        if hasattr(self, 'size'):
            self.resize()
        if hasattr(self, 'norm'):
            self.normalize()

        return self._img, self._joints

    def crop(self):
        # image cropping
        joints = self._joints.reshape((len(self._joints) / 2, 2))
        x, y, w, h = cv.boundingRect(np.asarray([joints.tolist()]))

        # bounding rect extending
        inf, sup = self.padding
        r = sup - inf
        pad_w_r = np.random.rand() * r + inf  # inf~sup
        pad_h_r = np.random.rand() * r + inf  # inf~sup
        x -= (w * pad_w_r - w) / 2
        y -= (h * pad_h_r - h) / 2
        w *= pad_w_r
        h *= pad_h_r

        # shifting
        if hasattr(self, 'shift'):
            x += np.random.rand() * self.shift * 2 - self.shift
            y += np.random.rand() * self.shift * 2 - self.shift

        # clipping
        x, y, w, h = [int(z) for z in [x, y, w, h]]
        x = np.clip(x, 0, self._img.shape[1] - 1)
        y = np.clip(y, 0, self._img.shape[0] - 1)
        w = np.clip(w, 1, self._img.shape[1] - (x + 1))
        h = np.clip(h, 1, self._img.shape[0] - (y + 1))
        self._img = self._img[y:y + h, x:x + w]

        # joint shifting
        joints = np.asarray([(j[0] - x, j[1] - y) for j in joints])
        self._joints = joints.flatten()

    def resize(self):
        if not isinstance(self.size, int):
            raise Exception('self.size should be int')
        orig_h, orig_w, _ = self._img.shape
        self._joints[0::2] = self._joints[0::2] / float(orig_w) * self.size
        self._joints[1::2] = self._joints[1::2] / float(orig_h) * self.size
        self._img = cv.resize(self._img, (self.size, self.size),
                              interpolation=cv.INTER_NEAREST)

    def normalize(self):
        if self.norm:
            # local contrast normalization
            for ch in range(self._img.shape[2]):
                self._img[ch] = (self._img[ch] - self._img[ch].mean()) / \
                    (np.std(self._img[ch]) + np.finfo(np.float32).eps)

            # joint pos normalization (-1.0 <= x, y <= 1.0)
            self._joints = (self._joints - self.size / 2.0) / float(self.size)

    def fliplr(self):
        if np.random.randint(2) == 1 and self.flip == True:
            self._img = np.fliplr(self._img)
            self._joints[0::2] = self._img.shape[1] - self._joints[0::2]

    def revert(self, pred):
        return (pred * self.size) + (self.size / 2)


if __name__ == '__main__':
    import csv
    line = csv.reader(open('data/panorama/joint_train.csv'))
    params = line.next()
    fname = 'data/panorama/images/' + params[1]
    image = cv.imread(fname)
    joints = np.asarray([int(p) for p in params[3:]])

    from create_panorama import draw_structure

    trans = Transform(padding=[1.5, 2.0])
    img, joints = trans.transform(image, joints)
    draw_structure(img, zip(joints[0::2], joints[1::2]))
    cv.imwrite('img0.jpg', img)
    img, joints = trans.transform(image, joints)
    cv.imwrite('img1.jpg', img)

    print joints
    import sys
    sys.exit()

    for i in range(10):
        img = train_data[i].transpose((1, 2, 0)) * 255
        img = img.astype(np.uint8)[:, :, ::-1]
        img = trans.transform(img)
        cv.imshow('test', img)
        cv.waitKey(0)
