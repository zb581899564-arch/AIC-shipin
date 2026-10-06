"""Sequential source ordinals, with the existing registered pixel identity."""
import hashlib


class SequentialReader:
    def __init__(self, source):
        import cv2
        self.cap = cv2.VideoCapture(str(source))
        if not self.cap.isOpened():
            raise RuntimeError('sequential source open failed')
        self.next_ordinal = 0
        self.last = None

    def read(self, ordinal, expected_sha, width, height):
        if type(ordinal) is not int or ordinal < 0 or ordinal < self.next_ordinal - 1:
            raise ValueError('invalid or backward source ordinal')
        while self.next_ordinal <= ordinal:
            ok, frame = self.cap.read()
            if not ok:
                raise RuntimeError('sequential source decode failed')
            self.last = frame
            self.next_ordinal += 1
        if self.last is None or self.last.shape != (height, width, 3):
            raise RuntimeError('sequential decoded geometry changed')
        digest = hashlib.sha256(memoryview(self.last).cast('B')).hexdigest()
        if digest != expected_sha:
            raise RuntimeError('registered decoded pixel identity not restored')
        return self.last.copy()

    def close(self):
        self.cap.release()
