from enum import StrEnum


class EventStatus(StrEnum):
    PUBLISHED = "published"
    REGISTRATION_CLOSED = "registration_closed"
    FINISHED = "finished"


class SyncStatus(StrEnum):
    NEVER = "never"
    SUCCESS = "success"
    FAILED = "failed"
