from enum import StrEnum


class EventStatus(StrEnum):
    PUBLISHED = "published"


class SyncStatus(StrEnum):
    NEVER = "never"
    SUCCESS = "success"
    FAILED = "failed"
