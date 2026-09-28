class ProcessingCancelled(Exception):
    """Raised when a user stops an in-progress fact check."""


def check_cancelled(cancel_event) -> None:
    if cancel_event is not None and cancel_event.is_set():
        raise ProcessingCancelled("Fact check stopped by user.")