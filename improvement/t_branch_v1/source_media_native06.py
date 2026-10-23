"""Unique first four-media admission chain; no training or future-stage launcher."""
import os

os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from media06 import main as acquire
from native07 import main as native_admission


def main():
    acquire()
    native_admission()


if __name__ == '__main__':
    main()
