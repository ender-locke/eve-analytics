class MissingSDEError(Exception):
    """
    Raised when the Static Data Export (SDE) is missing or not found
    at the expected location.

    This typically occurs when required EVE Online SDE files have not
    been downloaded or are not accessible by the application.

    Attributes:
        location (str): The path or location where the SDE was expected.
        message (str): Human-readable explanation of the error.
    """

    def __init__(self, location, message="you are missing the sde download"):
        """
        Initialize the MissingSDEError.

        Args:
            location (str): The expected location of the SDE files.
            message (str, optional): Base error message.
        """

        self.message = f"{message} -> {location}"
        super().__init__(self.message)

class NoMatchFoundError(Exception):

    def __init__(self, timestamp, message="no match data"):
        """
        """

        self.message = f"{message} for {timestamp}"
        super().__init__(self.message)


class MissingTimestampError(Exception):

    def __init__(self,):
        """
        Initialize the MissingTimestampError.

        """

        self.message = f"missing a timestamp "
        super().__init__(self.message)
