import time


class SeatsCache:
    def __init__(self, ttl: int = 30) -> None:
        self.ttl = ttl
        self._cache: dict[str, tuple[float, list[str]]] = {}

    def get(self, event_id: str) -> list[str] | None:
        cached = self._cache.get(event_id)

        if cached is None:
            return None

        expires_at, seats = cached

        if time.monotonic() >= expires_at:
            del self._cache[event_id]
            return None

        return seats

    def set(self, event_id: str, seats: list[str]) -> None:
        expires_at = time.monotonic() + self.ttl
        self._cache[event_id] = (expires_at, seats)