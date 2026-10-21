"""Two fixed 224-pixel views of the identical recovered, resized RGB."""
import numpy as np
from PIL import Image
from common import MEAN


def center_view(rgb):
    image = Image.fromarray(rgb)
    width, height = image.size
    # Match the integer-size CLIP short-side resize convention.
    size = (256, int(256 * height / width)) if width <= height else (int(256 * width / height), 256)
    image = image.resize(size, Image.Resampling.BICUBIC)
    left = round((image.width - 224) / 2)
    top = round((image.height - 224) / 2)
    return np.asarray(image.crop((left, top, left + 224, top + 224))).copy()


def full_view(rgb):
    image = Image.fromarray(rgb)
    width, height = image.size
    size = (max(1, round(224 * width / max(width, height))),
            max(1, round(224 * height / max(width, height))))
    image = image.resize(size, Image.Resampling.BICUBIC)
    canvas = Image.new('RGB', (224, 224), tuple(round(v * 255) for v in MEAN))
    left, top = (224 - size[0]) // 2, (224 - size[1]) // 2
    canvas.paste(image, (left, top))
    return np.asarray(canvas).copy(), dict(resized_size=list(size), paste_xy=[left, top],
                                         fill_pixels=224 * 224 - size[0] * size[1])


def contracts():
    # Unique border colors expose accidental crops or shifts in letterboxing.
    rgb = np.zeros((64, 128, 3), dtype=np.uint8)
    rgb[:, :16, 0] = 255
    rgb[:, -16:, 2] = 255
    full, info = full_view(rgb)
    assert info == dict(resized_size=[224, 112], paste_xy=[0, 56], fill_pixels=25088)
    assert full[112, 0, 0] == 255 and full[112, -1, 2] == 255
    assert (full[0, 0] == np.rint(np.asarray(MEAN) * 255)).all()
    assert center_view(rgb).shape == full.shape == (224, 224, 3)
    return dict(status='PASS_RENDERER_BORDER_FILL_AND_SHAPE', checks=4)
