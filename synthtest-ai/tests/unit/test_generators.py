from synthtest.gen.generators import primitives
from synthtest.util.rng import Rng


def test_int_range():
    rng = Rng.with_seed(123)
    for _ in range(100):
        value = primitives.generate_int(rng, 10, 20, "uniform")
        assert 10 <= value <= 20


def test_decimal_range():
    rng = Rng.with_seed(123)
    for _ in range(100):
        value = primitives.generate_decimal(rng, 1.5, 2.5, "normal")
        assert 1.5 <= value <= 2.5


def test_uuid_deterministic():
    rng1 = Rng.with_seed(42)
    rng2 = Rng.with_seed(42)
    assert primitives.generate_uuid(rng1) == primitives.generate_uuid(rng2)
