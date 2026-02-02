from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Iterable, Sequence

from .hashing import hash_to_int


@dataclass
class Rng:
    seed: int
    _rng: random.Random

    @classmethod
    def with_seed(cls, seed: int) -> "Rng":
        return cls(seed=seed, _rng=random.Random(seed))

    def derive(self, salt: str) -> "Rng":
        derived = hash_to_int(f"{self.seed}:{salt}")
        return Rng.with_seed(derived)

    def randint(self, a: int, b: int) -> int:
        return self._rng.randint(a, b)

    def random(self) -> float:
        return self._rng.random()

    def choice(self, seq: Sequence[Any]) -> Any:
        return self._rng.choice(seq)

    def choices(self, population: Sequence[Any], weights: Sequence[float] | None = None, k: int = 1) -> list[Any]:
        return self._rng.choices(population, weights=weights, k=k)

    def gauss(self, mu: float, sigma: float) -> float:
        return self._rng.gauss(mu, sigma)

    def lognormvariate(self, mu: float, sigma: float) -> float:
        return self._rng.lognormvariate(mu, sigma)

    def uniform(self, a: float, b: float) -> float:
        return self._rng.uniform(a, b)

    def getrandbits(self, k: int) -> int:
        return self._rng.getrandbits(k)
