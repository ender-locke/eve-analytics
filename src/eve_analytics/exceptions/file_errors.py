class MissingFilesError(Exception):
    """Exception raised when a files are missing is raised from the espn api"""
    def __init__(self, file_name, message="you are missing a file: "):
        self.file_name = file_name
        self.message = f"{message} {self.file_name})"
        super().__init__(self.message)

class LogLocationError(Exception):

    def __int__(self, message,location):
        self.location = location
        self.message = f"{message}: {location}"
        super().__init__(self.message)

class LogDirectoryNotSetError(Exception):

    def __int__(self):
        self.message = f"logs not set. please run set_log_directory or init class with directory"
        super().__init__(self.message)

