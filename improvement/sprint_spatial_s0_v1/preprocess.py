"""Author RGB/256 resize and normalization with registered legal proposals."""
import ast
import math
import cv2
import numpy as np
import torch
from control import ROOT


def encode_image(rgb):
    h, w = rgb.shape[:2]
    scale = 256. / min(h, w)
    resized_h, resized_w = int(round(h * scale / 32.) * 32), int(round(w * scale / 32.) * 32)
    image = (cv2.resize(rgb, (resized_w, resized_h)) / 256.).astype(np.float32)
    image -= np.array([.485, .456, .406], dtype=np.float32)
    image /= np.array([.229, .224, .225], dtype=np.float32)
    return torch.from_numpy(np.ascontiguousarray(image.transpose(2, 0, 1)))[None], resized_w / w, resized_h / h


def encode_rois(boxes, sx, sy):
    return torch.tensor([[0., math.floor(x * sx), math.floor(y * sy),
                         math.ceil((x + width) * sx), math.ceil((y + width * 9 / 16) * sy)]
                         for x, y, width in boxes], dtype=torch.float32)


def verify_author_preprocessing():
    tree = ast.parse((ROOT / 'author_runtime07/croppingDataset.py').read_text())
    selected = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'TransformFunctionTest']
    namespace = dict(cv2=cv2, np=np, RGB_MEAN=(.485, .456, .406), RGB_STD=(.229, .224, .225), generate_bboxes=lambda _: [])
    exec(compile(ast.Module(body=selected, type_ignores=[]), 'frozen_author_preprocess', 'exec'), namespace)
    rng = np.random.default_rng(20261021)
    for h, w in [(33, 57), (57, 33), (41, 41)]:
        rgb = rng.integers(0, 256, size=(h, w, 3), dtype=np.uint8)
        actual, _, _ = encode_image(rgb)
        expected, _, _ = namespace['TransformFunctionTest']()(rgb, 256.)
        if not np.array_equal(actual[0].numpy(), expected):
            raise ValueError('New input transform differs from exact author normalization')
    return dict(synthetic_cases=3, exact_author_image_values=True, research_images_repeated=0)
