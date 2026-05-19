from pathlib import Path
from eve_analytics.exceptions.file_errors import LogLocationError, LogDirectoryNotSetError
from eve_analytics.classes.parsed_logs import ParsedLogs
from eve_analytics.classes.db import Database
from eve_analytics.classes.analytics import MatchAnalytics
from eve_analytics.classes.flight_context import FlightContext

class EveAnalytics:
    """
    Main entry point for the Eve Analytics system.

    This class acts as the orchestration layer for:
    - Loading and validating log directories
    - Parsing raw EVE combat logs into structured data
    - Managing the database lifecycle and ingestion
    - Generating match-level analytics outputs

    It provides a high-level interface that coordinates parsing,
    storage, and analytics generation.

    Attributes:
        log_dir_location (Path | None): Directory containing log files.
        _parsed_logs (ParsedLogs | None): Parsed log data container.
        _db (Database): Database interface instance.
        _match_analytics (list[MatchAnalytics]): Generated analytics objects.
        _ctx (FlightContext): Shared flight context for analytics processing.
    """

    def __init__(self, log_directory=None):
        """
        Initializes the EveAnalytics client.

        Optionally sets the log directory and prepares the database.

        Args:
            log_directory (str | Path | None): Path to directory containing
                EVE log files. If not provided, must be set later.
        """
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
        Returns a string representation of the EveAnalytics instance.

        Returns:
            str: Basic identifier for the client.
        """

        return f"<EveAnalytics>"

    def set_log_directory(self, log_directory):
        """
        Sets the directory containing EVE log files.

        Args:
            log_directory (str | Path): Path to the log directory.

        Raises:
            LogLocationError: If the path is invalid or not a directory.
        """
        self._log_location(path=log_directory)

    def _log_location(self, path):
        """
        Validates and sets the internal log directory path.

        Args:
            path (str | Path): Path to validate.

        Raises:
            LogLocationError: If the path does not exist or is not a directory.
        """
        folder = Path(path)
        if not folder.exists():
            raise LogLocationError("Path does not exist", path)

        if not folder.is_dir():
            raise LogLocationError("Path is not a directory", path)


        self.log_dir_location = folder.resolve()

    def parse_logs(self):
        """
        Parses all log files in the configured directory.

        Raises:
            LogDirectoryNotSetError: If no log directory has been configured.
        """
        if self.log_dir_location is not None:
            self.__parsing_logs()
        else:
            raise LogDirectoryNotSetError()

    def __init_db(self):
        """
        Initializes the database instance for this client.
        """
        self.__create_ea_db()

    def __create_ea_db(self):
        """
        Creates the Database object associated with this client.
        """
        self._db = Database(self)

    @property
    def db(self):
        """
        Provides access to the database interface.

        Returns:
            Database: Active database instance.
        """
        return self._db

    @property
    def parsed_logs(self):
        """
        Returns parsed log data.

        Returns:
            ParsedLogs | None: Parsed logs if available.
        """
        return self._parsed_logs

    @property
    def match_analytics(self):
        """
        Returns generated match analytics objects.

        Returns:
            list[MatchAnalytics]: List of analytics results.
        """
        return self._match_analytics

    def __parsing_logs(self):
        """
        Internal method to instantiate and populate ParsedLogs.
        """
        parsed_logs = ParsedLogs(self.log_dir_location)
        self._parsed_logs = parsed_logs

    def load_db(self):
        """
        Loads parsed log data into the database.

        Executes the default ingestion pipeline, including:
        - Match insertion
        - Combat log insertion
        - EVE SDE data loading
        """
        self._db.default_db_load()
        #self.db.load_json(table=,
        #                  data=)

    def generate_analytics(self, match_id):
        """
        Generates analytics for a specific match.

        Args:
            match_id (str): Unique identifier of the match to analyze.

        Notes:
            Results are stored internally and can be retrieved via
            the match_analytics property.
        """
        self._match_analytics.append(MatchAnalytics(ea=self,
                                                    match_id=match_id,
                                                    fc=self._ctx))

    def save_analytics(self, save_dir):
        """
        Saves all generated analytics outputs to disk.

        Args:
            save_dir (str | Path): Directory where analytics files will be saved.
        """
        for match_analytics in self._match_analytics:
            match_analytics.save_analytics(save_dir)

    def add_match_comp_data(self, records: list):
        for record in records:
            self._db.insert_pilot_record(record=record)

    def get_match_ids(self, start_ts = None, end_ts = None, all: bool = True):
        if start_ts and end_ts:
            all = False
        match_ids = self.db._get_matches(start_ts=start_ts,
                                         end_ts=end_ts,
                                         all=all)
        return match_ids

