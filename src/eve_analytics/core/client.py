from pathlib import Path
from eve_analytics.exceptions.file_errors import LogLocationError, LogDirectoryNotSetError
from eve_analytics.classes.parser import Parser

class EveAnalytics:
    """
    Main client for interacting with the EveAnalytics API

    This class serves as the central point to get all of your tasty log data



    """

    def __init__(self, log_directory=None):
        self._parsed_logs = None
        if log_directory:
            self._log_location(path=log_directory)
        else:
            self.log_dir_location = None


    def __repr__(self) -> str:
        """

        :return:
        """

        return f"<EveAnalytics>"

    def set_log_directory(self, log_directory):
        self._log_location(path=log_directory)

    def _log_location(self, path):
        folder = Path(path)
        if not folder.exists():
            raise LogLocationError("Path does not exist", path)

        if not folder.is_dir():
            raise LogLocationError("Path is not a directory", path)


        self.log_dir_location = folder.resolve()

    def parse_logs(self):
        if self.log_dir_location is not None:
            self._parsing_logs()
        else:
            raise LogDirectoryNotSetError()

    @property
    def parsed_logs(self):
        return self._parsed_logs

    def _parsing_logs(self):
        parsed_logs = Parser(self.log_dir_location)
        self._parsed_logs = parsed_logs



