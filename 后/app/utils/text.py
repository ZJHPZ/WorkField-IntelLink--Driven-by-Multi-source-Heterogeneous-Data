"""文本处理工具 —— SimHash、jieba 分词、embedding 工具。

SimHash 用于 L2 去重（抄袭检测），jieba 用于中文分词。
"""

from __future__ import annotations

import re
from typing import Any


def tokenize(text: str) -> list[str]:
    """中文分词。优先 jieba，不可用时回退到简单正则切分。"""
    try:
        import jieba
        return [w for w in jieba.lcut(text) if len(w) > 1]
    except ImportError:
        return re.findall(r'[一-鿿]+|[a-zA-Z0-9+#.]+', text)


def deterministic_hash(token: str, hash_bits: int = 64) -> int:
    """DJB2 确定性 hash（跨进程可复现，不依赖 PYTHONHASHSEED）。"""
    h = 5381
    for ch in token:
        h = ((h << 5) + h + ord(ch)) & ((1 << hash_bits) - 1)
    return h


class SimHash:
    """手写 SimHash —— datasketch 不可用时的回退方案。"""

    def __init__(self, text: str, hash_bits: int = 64):
        self.hash_bits = hash_bits
        self.value = self._compute(text)

    def _compute(self, text: str) -> int:
        tokens = tokenize(text)
        if not tokens:
            return 0
        v = [0] * self.hash_bits
        for token in tokens:
            h = deterministic_hash(token, self.hash_bits)
            for i in range(self.hash_bits):
                if h & (1 << i):
                    v[i] += 1
                else:
                    v[i] -= 1
        fingerprint = 0
        for i in range(self.hash_bits):
            if v[i] > 0:
                fingerprint |= (1 << i)
        return fingerprint

    def distance(self, other: SimHash) -> int:
        """Hamming 距离。"""
        xor = self.value ^ other.value
        return bin(xor).count('1')


def sigmoid(x: float) -> float:
    """Sigmoid 函数。"""
    import math
    return 1 / (1 + math.exp(-x))
