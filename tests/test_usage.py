"""Tests for motoquant/usage.py — free-tier sim metering.

These exercise the real sqlite path (in-memory DB) including the atomic
ON CONFLICT increment, tier bypass, day rollover, and identity hashing.
"""

import sqlite3

import pytest

from motoquant import usage


@pytest.fixture()
def conn():
    c = sqlite3.connect(":memory:")
    yield c
    c.close()


class TestIdentity:
    def test_user_identity_shape(self):
        assert usage.user_identity(42) == "user:42"

    def test_anon_identity_is_hashed_and_stable(self):
        a = usage.anon_identity("203.0.113.7")
        b = usage.anon_identity("203.0.113.7")
        assert a == b
        assert a.startswith("anon:")
        # raw IP must not appear in the identity (privacy promise)
        assert "203.0.113.7" not in a

    def test_anon_identity_distinct_inputs(self):
        assert usage.anon_identity("a") != usage.anon_identity("b")

    def test_anon_identity_empty_falls_back(self):
        assert usage.anon_identity("").startswith("anon:")


class TestRecordAndCheck:
    def test_first_sim_counts_one(self, conn):
        st = usage.record_and_check(conn, "user:1", day="2026-07-02")
        assert st.count == 1
        assert st.allowed is True
        assert st.limit == usage.FREE_DAILY_SIMS
        assert st.remaining == usage.FREE_DAILY_SIMS - 1

    def test_increments_atomically(self, conn):
        for i in range(5):
            st = usage.record_and_check(conn, "user:1", day="2026-07-02")
        assert st.count == 5

    def test_quota_exceeded_blocks_free_tier(self, conn):
        for _ in range(usage.FREE_DAILY_SIMS):
            st = usage.record_and_check(conn, "anon:x", day="2026-07-02")
        assert st.allowed is True
        st = usage.record_and_check(conn, "anon:x", day="2026-07-02")
        assert st.allowed is False
        assert st.remaining == 0

    def test_paid_tiers_never_blocked_but_still_counted(self, conn):
        for _ in range(usage.FREE_DAILY_SIMS + 5):
            st = usage.record_and_check(conn, "user:2", tier="pro", day="2026-07-02")
        assert st.allowed is True
        assert st.limit is None
        assert st.remaining is None
        assert st.count == usage.FREE_DAILY_SIMS + 5

    def test_studio_tier_unlimited(self, conn):
        st = usage.record_and_check(conn, "user:3", tier="studio", day="2026-07-02")
        assert st.allowed is True and st.limit is None

    def test_day_rollover_resets_count(self, conn):
        for _ in range(3):
            usage.record_and_check(conn, "user:1", day="2026-07-01")
        st = usage.record_and_check(conn, "user:1", day="2026-07-02")
        assert st.count == 1

    def test_identities_are_isolated(self, conn):
        usage.record_and_check(conn, "user:1", day="2026-07-02")
        st = usage.record_and_check(conn, "user:2", day="2026-07-02")
        assert st.count == 1

    def test_default_day_is_utc_today(self, conn):
        st = usage.record_and_check(conn, "user:9")
        assert st.count == 1
        assert usage.peek(conn, "user:9") == 1


class TestBatchCharge:
    """``n`` — routes that run more than one RK4 pass per request.

    /api/simulate/compare runs two, a classic chat turn's rank/choose
    dispatch runs up to 25, and an agent heavy op costs a nominal batch.
    Before this they either charged 1 (understating the quota) or nothing
    at all (2026-07-25 audit §3.4/§3.5).
    """

    def test_n_charges_that_many_units(self, conn):
        st = usage.record_and_check(conn, "user:1", day="2026-07-02", n=2)
        assert st.count == 2
        assert st.remaining == usage.FREE_DAILY_SIMS - 2

    def test_n_accumulates_on_an_existing_row(self, conn):
        usage.record_and_check(conn, "user:1", day="2026-07-02", n=3)
        st = usage.record_and_check(conn, "user:1", day="2026-07-02", n=4)
        assert st.count == 7

    def test_default_is_still_one(self, conn):
        st = usage.record_and_check(conn, "user:1", day="2026-07-02")
        assert st.count == 1

    def test_batch_can_cross_the_quota_line(self, conn):
        st = usage.record_and_check(
            conn, "anon:x", day="2026-07-02", n=usage.FREE_DAILY_SIMS + 1
        )
        assert st.allowed is False
        assert st.remaining == 0

    def test_zero_or_negative_never_decrements(self, conn):
        usage.record_and_check(conn, "user:1", day="2026-07-02", n=5)
        st = usage.record_and_check(conn, "user:1", day="2026-07-02", n=0)
        assert st.count == 6  # clamped to a minimum charge of 1
        st = usage.record_and_check(conn, "user:1", day="2026-07-02", n=-10)
        assert st.count == 7

    def test_paid_tier_batch_is_counted_but_never_blocked(self, conn):
        st = usage.record_and_check(conn, "user:2", tier="pro", day="2026-07-02", n=40)
        assert st.count == 40
        assert st.allowed is True
        assert st.limit is None


class TestPeek:
    def test_peek_without_rows(self, conn):
        assert usage.peek(conn, "user:404", day="2026-07-02") == 0

    def test_peek_does_not_increment(self, conn):
        usage.record_and_check(conn, "user:1", day="2026-07-02")
        assert usage.peek(conn, "user:1", day="2026-07-02") == 1
        assert usage.peek(conn, "user:1", day="2026-07-02") == 1
