class MissingSDEError(Exception):
    """Exception raised when a files are missing is raised from the espn api"""
    def __init__(self, location, message="you are missing the sde download"):
        self.message = f"{message} -> {location}"
        super().__init__(self.message)

