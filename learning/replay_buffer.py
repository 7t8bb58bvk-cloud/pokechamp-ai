from __future__ import annotations
from collections import deque
import random


class ReplayBuffer:
    def __init__(self, capacity: int = 10_000):
        self.capacity = capacity
        self.buffer = deque(maxlen=capacity)

    def add(self, item):
        self.buffer.append(item)

    def sample(self, batch_size: int):
        batch_size = min(batch_size, len(self.buffer))
        return random.sample(list(self.buffer), batch_size)

    def __len__(self):
        return len(self.buffer)
