from pathlib import Path
from eve_analytics.exceptions.file_errors import LogLocationError, LogDirectoryNotSetError
from eve_analytics.classes.parsed_logs import ParsedLogs
from eve_analytics.classes.db import Database
from eve_analytics.classes.analytics import MatchAnalytics
from eve_analytics.classes.flight_context import FlightContext

class EveAnalytics:
    """
    Main client for interacting with the EveAnalytics API

    This class serves as the central point to get all of your tasty log data



    """

    def __init__(self, log_directory=None):
        self._parsed_logs = None
        self._match_analytics = []
        self._ctx = FlightContext()
        if log_directory:
            self._log_location(path=log_directory)
        else:
            self.log_dir_location = None
        self.__init_db()


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
            self.__parsing_logs()
        else:
            raise LogDirectoryNotSetError()

    def __init_db(self):
        self.__create_ea_db()

    def __create_ea_db(self):
        self._db = Database(self)

    @property
    def db(self):
        return self._db

    @property
    def parsed_logs(self):
        return self._parsed_logs

    @property
    def match_analytics(self):
        return self._match_analytics

    def __parsing_logs(self):
        parsed_logs = ParsedLogs(self.log_dir_location)
        self._parsed_logs = parsed_logs

    def load_db(self):
        self._db.default_db_load()
        #self.db.load_json(table=,
        #                  data=)

    def generate_analytics(self, match_id):
        self._match_analytics.append(MatchAnalytics(ea=self,
                                                    match_id=match_id,
                                                    fc=self._ctx))

    def save_analytics(self, save_dir):
        for match_analytics in self._match_analytics:
            match_analytics.save_analytics(save_dir)
