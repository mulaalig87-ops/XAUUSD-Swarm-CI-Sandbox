"""WP9-02 review R2-01: one numeric check everywhere — bool refused, huge int refused (no OverflowError)."""
import pathlib
import re

import pytest

from xauusd_swarm import controls, court, discovery, evidence, inventory, nulls, slicing
from xauusd_swarm.numeric import finite_real
from xauusd_swarm.representations import ReprError, log_returns

BAD = [True, False, float("nan"), float("inf"), float("-inf"), 10 ** 400, -(10 ** 400), "1", None, [1]]


@pytest.mark.parametrize("x", BAD)
def test_finite_real_refuses(x):
    assert finite_real(x) is False


@pytest.mark.parametrize("x", [0, 1, -2.5, 10 ** 300, 1e308])
def test_finite_real_accepts(x):
    assert finite_real(x) is True


@pytest.mark.parametrize("fn", [controls._num, court._num, evidence._num, slicing._num, inventory.valid_time,
                                nulls._finite, discovery._finite_pos])
@pytest.mark.parametrize("x", BAD)
def test_every_module_check_refuses_without_raising(fn, x):
    assert fn(x) is False


@pytest.mark.parametrize("p", [True, 10 ** 400, float("nan"), 0, -1.0])
def test_representation_prices_refused(p):
    with pytest.raises(ReprError):
        log_returns([1.0, p, 1.2])


@pytest.mark.parametrize("scale", [True, 10 ** 400, float("inf")])
def test_representation_scale_refused(scale):
    with pytest.raises(ReprError):
        log_returns([1.0, 1.1, 1.2], scale=scale)


def test_no_module_calls_isfinite_directly_on_inputs():
    """Sweep guard: outside numeric.py, isfinite( appears only on values that are already floats:
    discovery.filled (floats only), representations._out (transform outputs), the statement guard
    (floats only) and rip1_attack._lse (an internal log-likelihood maximum, RIP-1)."""
    src = pathlib.Path(finite_real.__code__.co_filename).parent
    hits = [(p.name, ln.strip()) for p in sorted(src.glob("*.py")) if p.name != "numeric.py"
            for ln in p.read_text(encoding="utf-8").splitlines() if re.search(r"\bisfinite\(", ln)]
    assert hits == [("discovery.py", "return math.isfinite(v)"),
                    ("representations.py", "if any(not math.isfinite(v) for v in values):"),
                    ("rip1_attack.py", "return m + math.log(np.sum(np.exp(v - m))) if np.isfinite(m) else -math.inf"),
                    ("statement_guard.py", "if isinstance(v, float) and not math.isfinite(v):")]


# ---------------- R3-01: every numeric parameter of the representation transforms ----------------
from xauusd_swarm.representations import activity_time, affine_level, level_residual, tick_grid  # noqa: E402

BADP = [True, float("nan"), float("inf"), float("-inf"), 10 ** 400, "1", None]
PR = [100.0, 100.5, 101.0]


@pytest.mark.parametrize("v", BADP)
@pytest.mark.parametrize("call", [lambda v: tick_grid(PR, v, 0.01), lambda v: tick_grid(PR, 100.0, v),
                                  lambda v: level_residual(PR, v), lambda v: affine_level(PR, v, 0.0),
                                  lambda v: affine_level(PR, 1.0, v)],
                         ids=["tick_grid.c", "tick_grid.delta", "level_residual.m", "affine.a", "affine.b"])
def test_r3_01_transform_parameters_refused(call, v):
    with pytest.raises(ReprError):
        call(v)


@pytest.mark.parametrize("n", [True, False, -1, 1.0, "3", None])
def test_r3_01_activity_time_refuses_bool_and_non_int(n):
    with pytest.raises(ReprError):
        activity_time(n)


def test_s3_01_transform_overflow_is_refused():
    with pytest.raises(ReprError, match="non-finite"):
        affine_level(PR, 1e308, 0.0)
    with pytest.raises(ReprError, match="non-finite"):
        tick_grid(PR, 0.0, 1e-320)


def test_valid_transforms_still_work():
    assert tick_grid(PR, 100.0, 0.5) == [0.0, 1.0, 2.0]
    assert affine_level(PR, 2, 1) == [201.0, 202.0, 203.0]
    assert activity_time(3) == [0, 1, 2]


# ---------------- S3-02 / S3-03 / S3-04: same class elsewhere ----------------
@pytest.mark.parametrize("k", ["c", "a", "b", "m"])
@pytest.mark.parametrize("v", [True, float("nan"), float("inf"), 10 ** 400])
def test_s3_02_vault_parameters_refused(k, v):
    from xauusd_swarm.charter import GateError
    from xauusd_swarm.custody import Vault
    p = {"c": 1.0, "a": 1.0, "b": 0.0, "m": 3.0, k: v}
    with pytest.raises(GateError):
        Vault().set_params("F1", **p)


@pytest.mark.parametrize("t", [float("nan"), True, None, 10 ** 400])
def test_s3_03_leak_check_refuses_unknown_times(t):
    """A NaN time used to make every comparison False, so the leak check passed silently."""
    from xauusd_swarm.slicing import LeakError, assert_no_leak
    with pytest.raises(LeakError):
        assert_no_leak(t, [1.0])
    with pytest.raises(LeakError):
        assert_no_leak(10.0, [1.0, t])


@pytest.mark.parametrize("kw", [{"iterations": True}, {"iterations": 0}, {"iterations": 2.0}])
def test_s3_04_iaaft_iterations(kw):
    import random
    with pytest.raises(nulls.NullError):
        nulls.iaaft([1.0, 2.0, 3.0, 4.0], random.Random(0), **kw)


@pytest.mark.parametrize("kw", [{"n": True}, {"n": 1}, {"tol": float("nan")}, {"tol": -1.0}, {"tol": True}])
def test_s3_04_zero_cond_mean_arguments(kw):
    import random
    args = {"n": 5, "tol": 1e-12, **kw}
    with pytest.raises(nulls.NullError):
        nulls.zero_cond_mean(lambda n, r: ([0.0] * n, [0.0] * n), args["n"], random.Random(0), tol=args["tol"])
