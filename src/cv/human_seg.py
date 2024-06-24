import cv2
import os
import cv2
import argparse
import numpy as np
import onnxruntime


class HumanSeg:
    def __init__(self, image_path, model_path):
        image = cv2.imread(image_path)
        self.image = image
        self.model_path = model_path

    # Get x_scale_factor & y_scale_factor to resize image
    def get_scale_factor(self, im_h, im_w, ref_size):

        if max(im_h, im_w) < ref_size or min(im_h, im_w) > ref_size:
            if im_w >= im_h:
                im_rh = ref_size
                im_rw = int(im_w / im_h * ref_size)
            elif im_w < im_h:
                im_rw = ref_size
                im_rh = int(im_h / im_w * ref_size)
        else:
            im_rh = im_h
            im_rw = im_w

        im_rw = im_rw - im_rw % 32
        im_rh = im_rh - im_rh % 32

        x_scale_factor = im_rw / im_w
        y_scale_factor = im_rh / im_h

        return x_scale_factor, y_scale_factor


    def image_preprocess(self, im, ref_size=512):
        # unify image channels to 3
        if len(im.shape) == 2:
            im = im[:, :, None]
        if im.shape[2] == 1:
            im = np.repeat(im, 3, axis=2)
        elif im.shape[2] == 4:
            im = im[:, :, 0:3]

        # normalize values to scale it between -1 to 1
        im = (im - 127.5) / 127.5

        im_h, im_w, im_c = im.shape
        x, y = self.get_scale_factor(im_h, im_w, ref_size)

        # resize image
        im = cv2.resize(im, None, fx=x, fy=y, interpolation=cv2.INTER_AREA)

        # prepare input shape
        im = np.transpose(im)
        im = np.swapaxes(im, 1, 2)
        im = np.expand_dims(im, axis=0).astype('float32')

        return im, im_w, im_h


    def compose_image(self, im, matte):
        im_h, im_w, im_c = im.shape
        matte = cv2.resize(matte, dsize=(im_w, im_h), interpolation=cv2.INTER_AREA)
        b, g, r = cv2.split(im)
        result = cv2.merge([r, g, b, matte])

        return result


    def onnx_inference(self, model_path, im):
        session = onnxruntime.InferenceSession(model_path, None)
        input_name = session.get_inputs()[0].name
        output_name = session.get_outputs()[0].name
        result = session.run([output_name], {input_name: im})
        return result


    def image_postprocess(self, matte, im_w, im_h):
        # refine matte
        matte = (np.squeeze(matte) * 255).astype('uint8')
        matte = cv2.resize(matte, dsize=(im_w, im_h), interpolation=cv2.INTER_AREA)
        return matte


    def inference(self, ref_size = 512):
        im = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        im_pre, im_w, im_h = self.image_preprocess(im, ref_size)
        result = self.onnx_inference(self.model_path, im_pre)
        mask = self.image_postprocess(result[0], im_w, im_h)
        # compose_im = self.compose_image(im, mask)
        res = cv2.bitwise_and(im, im, mask=mask)
        res = cv2.cvtColor(res, cv2.COLOR_BGR2RGB)
        return res


if __name__ == '__main__':
    human_seg = HumanSeg(image_path="C:\\Repo\\ConceptVisDemo\\save\\lec.png", model_path="C:\Repo\ConceptVisDemo\src\cv\modnet_photographic_portrait_matting.onnx")
    res = human_seg.inference()
    cv2.imwrite('save\\seg.jpg', res)
    cv2.imshow('hsv', res)
    #关闭窗口
    cv2.waitKey(0)
    #销毁内存
    cv2.destroyAllWindows()


