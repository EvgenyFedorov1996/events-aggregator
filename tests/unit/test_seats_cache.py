import time

from app.cache.seats import SeatsCache


def test_cache_returns_saved_seats():
    cache = SeatsCache(ttl=30)
    seats = ["A1", "A2", "B1"]

    cache.set("event-1", seats)

    assert cache.get("event-1") == seats


def test_cache_returns_none_for_missing_event():
    cache = SeatsCache(ttl=30)

    assert cache.get("event-1") is None


def test_cache_expires():
    cache = SeatsCache(ttl=0)
    seats = ["A1"]

    cache.set("event-1", seats)

    time.sleep(0.01)

    assert cache.get("event-1") is None
