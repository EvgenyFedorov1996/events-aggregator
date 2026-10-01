class EventNotFound(Exception):
    """Raised when an event does not exist."""


class RegistrationClosed(Exception):
    """Raised when registration for an event is closed."""


class SeatNotAvailable(Exception):
    """Raised when the requested seat is unavailable."""


class TicketNotFound(Exception):
    """Raised when a ticket does not exist."""
