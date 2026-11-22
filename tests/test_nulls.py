"""G3: properties of the §11.2 card generators (what each preserves and breaks). SYNTHETIC ONLY.

These are generator property tests, not the TP-21/tool controls (those run each card on planted worlds
and are a separate component); TP-81 and TP-82 are also separate experiments.
"""
import math
import random

import pytest

from xauusd_swarm.nulls import (CARDS, NullError, amplitude_spectrum, block_bootstrap, full_shuffle, iaaft,
                                null_generator, pair_shuffle_blocks, signs, time_reversal, zero_cond_mean)


def ar1(n, phi, seed):
    rnd, x, out = random.Random(seed), 0.0, []
    for _ in range(n):
        x = phi * x + rnd.gauss(0, 1)
        out.append(x)
    return out


def acf1(x):
    m = sum(x) / len(x)
    d = [v - m for v in x]
    return sum(d[i] * d[i + 1] for i in range(len(d) - 1)) / sum(v * v for v in d)


def test_six_cards_as_in_11_2():
    assert set(CARDS) == {"full_shuffle", "iaaft", "pair_shuffle_vol_blocks", "block_bootstrap",
                          "zero_cond_mean", "time_reversal"}
    assert [c for c, v in CARDS.items() if not v["is_null"]] == ["block_bootstrap"]


def test_full_shuffle_keeps_marginal_breaks_dependence():
    x = ar1(400, 0.8, 1)
    y = full_shuffle(x, random.Random(2))
    assert sorted(y) == sorted(x)
    assert acf1(x) > 0.6 and abs(acf1(y)) < 0.2
    assert full_shuffle(x, random.Random(2)) == y                     # deterministic by seed


def test_time_reversal_exact():
    x = ar1(50, 0.3, 3)
    assert time_reversal(x) == x[::-1] and time_reversal(time_reversal(x)) == x


def test_iaaft_keeps_marginal_exactly_and_spectrum_approximately():
    x = [v ** 3 for v in ar1(128, 0.7, 4)]                            # monotone transform of a linear process
    y = iaaft(x, random.Random(5), iterations=60)
    assert sorted(y) == sorted(x)                                     # marginal exact
    ax, ay = amplitude_spectrum(x), amplitude_spectrum(y)
    rel = math.sqrt(sum((p - q) ** 2 for p, q in zip(ax, ay)) / sum(p * p for p in ax))
    shuffled = amplitude_spectrum(full_shuffle(x, random.Random(5)))
    rel_shuffle = math.sqrt(sum((p - q) ** 2 for p, q in zip(ax, shuffled)) / sum(p * p for p in ax))
    assert rel < 0.25 and rel < rel_shuffle / 2                       # spectrum kept (approximately)
    assert y != x                                                     # a different realisation


def test_iaaft_non_power_of_two_length():
    x = ar1(30, 0.5, 6)
    assert sorted(iaaft(x, random.Random(7), iterations=10)) == sorted(x)


def test_pair_shuffle_stays_within_blocks_and_keeps_pairs():
    rnd = random.Random(8)
    s = [rnd.choice((-1, 1)) for _ in range(60)]
    a = [rnd.random() for _ in range(60)]
    blocks = ["lo"] * 30 + ["hi"] * 30
    s2, a2 = pair_shuffle_blocks(s, a, blocks, random.Random(9))
    for lab in ("lo", "hi"):
        ids = [i for i, b in enumerate(blocks) if b == lab]
        assert sorted(zip((s[i] for i in ids), (a[i] for i in ids))) == \
               sorted(zip((s2[i] for i in ids), (a2[i] for i in ids)))    # joint (sign, size) kept per block
    assert (s2, a2) != (s, a)
    with pytest.raises(NullError, match="±1"):
        pair_shuffle_blocks([0, 1], [0.1, 0.2], ["x", "x"], random.Random(1))


def test_block_bootstrap_is_not_a_null_and_needs_b():
    with pytest.raises(NullError, match="not a null"):
        null_generator("block_bootstrap")
    x = ar1(100, 0.5, 10)
    with pytest.raises(NullError, match="given explicitly"):
        block_bootstrap(x, 0, random.Random(1))
    y = block_bootstrap(x, 10, random.Random(1))
    assert len(y) == 100 and set(y) <= set(x)


def test_zero_cond_mean_wrapper_refuses_nonzero_conditional_mean():
    def ok(n, rng):                                                   # registered simulator (fixture)
        return [rng.gauss(0, 1) for _ in range(n)], [0.0] * n

    def bad(n, rng):
        r = [rng.gauss(0, 1) for _ in range(n)]
        return r, [0.1 * v for v in [0.0] + r[:-1]]                  # E[r_t | past] = 0.1 r_{t-1}
    assert len(zero_cond_mean(ok, 20, random.Random(1))) == 20
    with pytest.raises(NullError, match="E\\[r_t \\| past\\] = 0"):
        zero_cond_mean(bad, 20, random.Random(1))


def test_signs_exclude_zero_returns_and_count_them():
    assert signs([0.1, 0.0, -0.2, 0.0]) == ([1, -1], 2)


def test_input_checks():
    for bad in ([], [1.0], [1.0, float("nan")], [1, True]):
        with pytest.raises(NullError):
            full_shuffle(bad, random.Random(0))
    with pytest.raises(NullError, match="unknown card"):
        null_generator("lens")
    assert null_generator("full_shuffle") is full_shuffle


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf"), True])
def test_r1_01_zero_cond_mean_refuses_invalid_conditional_means(bad):
    def sim(n, rng):
        return [rng.gauss(0, 1) for _ in range(n)], [0.0] * (n - 1) + [bad]
    with pytest.raises(NullError, match="finite number"):
        zero_cond_mean(sim, 10, random.Random(1))


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), True, -0.1])
def test_r1_02_pair_magnitudes_finite_nonnegative_not_bool(bad):
    with pytest.raises(NullError, match="finite, non-negative"):
        pair_shuffle_blocks([1, -1], [0.1, bad], ["x", "x"], random.Random(1))


def test_s1_01_signs_refuse_nan():
    with pytest.raises(NullError):
        signs([0.1, float("nan")])


def test_s1_03_huge_int_is_refused_not_overflow():
    with pytest.raises(NullError):
        full_shuffle([1, 10 ** 400], random.Random(0))


@pytest.mark.parametrize("bad", [True, float("inf"), float("nan"), 0, -1])
def test_s1_02_log_returns_scale_finite_positive(bad):
    from xauusd_swarm.representations import ReprError, log_returns
    with pytest.raises(ReprError):
        log_returns([1.0, 1.1, 1.2], scale=bad)
