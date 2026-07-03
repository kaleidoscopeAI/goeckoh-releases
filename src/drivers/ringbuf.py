import numpy as np
import threading


class DropRingBuffer:
    """
    Bounded float32 ring buffer with drop-not-block semantics.
    Thread-safe via a short lock around index updates only.

    - push(): if full, drops newest chunk (returns False)
    - pop(): returns None if empty
    """

    def __init__(self, capacity_frames: int, frame_size: int):
        self.capacity = int(capacity_frames)
        self.frame_size = int(frame_size)
        self.buf = np.zeros((self.capacity, self.frame_size), dtype=np.float32)
        self.w = 0
        self.r = 0
        self.count = 0
        self.lock = threading.Lock()

    def push(self, frame: np.ndarray) -> bool:
        if frame.shape[0] != self.frame_size:
            raise ValueError("bad frame size")
        with self.lock:
            if self.count >= self.capacity:
                return False  # drop
            self.buf[self.w, :] = frame
            self.w = (self.w + 1) % self.capacity
            self.count += 1
            return True

    def pop(self):
        with self.lock:
            if self.count <= 0:
                return None
            out = self.buf[self.r, :].copy()
            self.r = (self.r + 1) % self.capacity
            self.count -= 1
            return out

    def size(self) -> int:
        with self.lock:
            return self.count
