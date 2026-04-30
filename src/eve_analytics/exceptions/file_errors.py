class MissingFilesError(Exception):
    """
    Raised when a required file is missing from the ESPN API or local environment.

    Attributes:
        file_name (str): The name of the missing file.
        message (str): Human-readable explanation of the error.
    """
    def __init__(self, file_name, message="you are missing a file: "):
        """
        Initialize the MissingFilesError.

        Args:
            file_name (str): The name of the missing file.
            message (str, optional): Base error message. Defaults to "You are missing a file:".
        """
        self.file_name = file_name
        self.message = f"{message} {self.file_name})"
        super().__init__(self.message)

class LogLocationError(Exception):
    """
    Raised when an invalid or inaccessible log file location is provided.

    Attributes:
        location (str): The problematic file or directory path.
        message (str): Human-readable explanation of the error.
    """
    def __int__(self, message,location):
        """
        Initialize the LogLocationError.

        Args:
            message (str): Description of the error.
            location (str): The invalid or inaccessible path.
        """
        self.location = location
        self.message = f"{message}: {location}"
        super().__init__(self.message)

class LogDirectoryNotSetError(Exception):
    """
    Raised when a log directory is required but has not been configured.

    This typically occurs when attempting to access or process logs before
    calling a setup method like `set_log_directory()` or initializing the
    class with a valid directory.
    """

    def __int__(self):
        """
        Initialize the LogDirectoryNotSetError with a default message.
        """
        self.message = f"logs not set. please run set_log_directory or init class with directory"
        super().__init__(self.message)

