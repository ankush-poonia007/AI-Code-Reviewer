class ServiceError(Exception):
    """Base exception for all service layer errors."""
    pass


class ReviewNotFoundError(ServiceError):
    """Raised when a requested review record cannot be found in the database."""
    def __init__(self, review_id: str) -> None:
        self.review_id = review_id
        super().__init__(f"Review with ID {review_id} not found.")


class ExecutionNotFoundError(ServiceError):
    """Raised when execution metadata is requested but not found for a review."""
    def __init__(self, review_id: str) -> None:
        self.review_id = review_id
        super().__init__(f"Execution metadata not found for review ID {review_id}.")
