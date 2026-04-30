from eve_analytics.ingest.splicer import parse_combat_log
from eve_analytics.ingest.matches import parse_match_intervals
from eve_analytics.exceptions.file_errors import MissingFilesError
from eve_analytics.classes.json_log_data import JSONLogData
from eve_analytics.data.logs import log_keys
import hashlib
from datetime import timedelta, timezone
import pandas as pd


class ParsedLogs:
    """
    Parses EVE combat and local logs into structured match-based datasets.

    This class is responsible for:
    - Loading combat log files and a local log file from a directory
    - Determining match time intervals from the local log
    - Parsing combat logs into categorized event lists (damage, reps, neuts, etc.)
    - Assigning each event to a match based on timestamp matching
    - Converting parsed data into pandas DataFrames and JSON outputs

    Attributes:
        folder (Path): Directory containing log files.
        combat_logs (list[Path]): List of combat log file paths.
        local_log (Path): Path to the local log file.
        matches (list[dict]): Parsed match intervals with metadata.
        logs_parsed (bool): Whether logs have been successfully parsed.
        all_* (list): Aggregated event lists across all logs.
        all_unique_pilots (list): Unique pilot names found in logs.
        _log_dfs (dict): Dictionary of pandas DataFrames per log category.
        jsons (list): Serialized JSON outputs of parsed DataFrames.
        export_date (datetime): Timestamp used for export reference.
    """

    def __init__(self, folder):
        """
        Initializes ParsedLogs and immediately processes log files.

        Workflow:
        1. Scans folder for combat and local logs
        2. Determines match intervals from local log
        3. Parses combat logs into structured event data

        Args:
            folder (Path): Directory containing EVE log files.
        """
        self.folder = folder
        self._log_dfs = None
        self.all_nos = None
        self.all_neuts = None
        self.all_dmg = None
        self.all_reps = None
        self.all_scrams = None
        self.all_cap_warnings = None
        self.all_skipped = None
        self.all_jams = None
        self.all_drones = None
        self.all_reloads = None
        self.all_links = None
        self.all_cap_reps = None
        self.logs_parsed = False
        self.all_unique_pilots = None
        self.jsons = []
        self.__set_files()
        self.__determine_matches()
        self.__parse_combat_logs()

    def __repr__(self) -> str:
        """
        Returns a string representation of the ParsedLogs instance.

        Returns:
            str: Summary of folder and parsing state.
        """

        return f"<ParsedLogs> {self.folder} | logs parsed -> {self.logs_parsed}"

    @property
    def log_dfs(self):
        """
        Returns the dictionary of generated pandas DataFrames.

        Returns:
            dict[str, pd.DataFrame]: Parsed log data grouped by category.
        """
        return self._log_dfs

    def __set_files(self):
        """
        Identifies and separates combat log files and local log file.

        Raises:
            MissingFilesError: If combat logs or local log are not found.
        """
        txt_files = list(self.folder.glob("*.txt"))
        combat_files = []
        local_file = None

        for file in txt_files:
            if "local" in file.name.lower():
                local_file = file
            else:
                combat_files.append(file)

        if not combat_files:
            MissingFilesError("combat logs")
        if local_file is None:
            MissingFilesError("local log")

        self.combat_logs = combat_files
        self.local_log = local_file


    def __determine_matches(self):
        """
        Parses match intervals from the local log and builds match metadata.

        Each match includes:
        - A unique hash ID
        - Start and end timestamps
        - A countdown start buffer
        - A human-readable description
        """
        match_intervals = parse_match_intervals(self.local_log)
        matches = []
        for idx, (start, end,) in enumerate(match_intervals):
            match_num = idx + 1
            matches.append({
                "idx": match_num,
                "id": hashlib.sha256(f"{start}:{end}".encode()).hexdigest(),
                "countdown": start - timedelta(seconds=15),
                "start": start,
                "end": end,
                "description": f"match {match_num}",
                "add_row": True
            })

        self.matches = matches
        self.export_date = matches[0]['start']

    def __to_utc(self, dt):
        """
        Converts a datetime object to UTC.

        Args:
            dt (datetime): Input datetime (naive or timezone-aware).

        Returns:
            datetime: UTC-normalized datetime.
        """
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)  # assume it's UTC
        return dt.astimezone(timezone.utc)

    def __get_match_id(self, ts):
        """
        Determines which match a timestamp belongs to.

        A tolerance window of ±15 seconds is applied to match boundaries.

        Args:
            ts (datetime): Event timestamp.

        Returns:
            str: Match ID if found, otherwise "unknown".
        """
        timestamp = self.__to_utc(ts)
        TOLERANCE = timedelta(seconds=15)

        for m in self.matches:
            start = self.__to_utc(m["start"])
            end = self.__to_utc(m["end"])

            if (start - TOLERANCE) <= timestamp <= (end + TOLERANCE):
                return m["id"]

        return "unknown"


    def __parse_combat_logs(self):
        """
        Parses all combat log files and aggregates event data.

        For each combat log:
        - Parses structured event categories (damage, reps, neuts, etc.)
        - Assigns each event to a match ID based on timestamp
        - Collects unique pilots across all logs
        - Aggregates results into class-level lists
        """
        all_neuts = []
        all_dmg = []
        all_reps = []
        all_nos = []
        all_scrams = []
        all_jams = []
        all_drones = []
        all_links = []
        all_reloads = []
        all_cap_warnings = []
        all_skipped = []
        all_cap_reps = []
        unique_pilots = []
        for path in self.combat_logs:
            combat_logs = parse_combat_log(path)

            for key in log_keys:
                for entry in combat_logs[key]:
                    try:
                        entry["match_id"] = self.__get_match_id(entry["time"])
                    except KeyError as e:
                        print(e)

            all_nos.extend(combat_logs["nos"])
            all_neuts.extend(combat_logs['neut'])
            all_dmg.extend(combat_logs['dmg'])
            all_reps.extend(combat_logs['reps'])
            all_scrams.extend(combat_logs["scrams"])
            all_cap_warnings.extend(combat_logs["cap_warning"])
            all_skipped.extend(combat_logs['skipped'])
            all_jams.extend(combat_logs['jams'])
            all_drones.extend(combat_logs['drones'])
            all_reloads.extend(combat_logs['reloads'])
            all_links.extend(combat_logs['links'])
            all_cap_reps.extend(combat_logs['cap_reps'])

            for pilot in combat_logs['pilots']:
                if pilot not in unique_pilots:
                    unique_pilots.append(pilot)

            self.all_nos = all_nos
            self.all_neuts = all_neuts
            self.all_dmg = all_dmg
            self.all_reps = all_reps
            self.all_scrams = all_scrams
            self.all_cap_warnings = all_cap_warnings
            self.all_skipped = all_skipped
            self.all_jams = all_jams
            self.all_drones = all_drones
            self.all_reloads = all_reloads
            self.all_links = all_links
            self.all_cap_reps = all_cap_reps
            self.all_unique_pilots = unique_pilots
            self.logs_parsed = True

    def generate_dfs(self):
        """
        Generates pandas DataFrames from parsed log data.

        This must be called after logs have been parsed.
        """
        self.__generate_log_dfs()

    def generate_jsons(self):
        """
        Converts all generated DataFrames into JSON format.

        Each DataFrame is serialized into a JSON string using:
            orient="records"

        Stores results in self.jsons as a list of:
            {
                "filename": str,
                "data": str (JSON),
                "key": str
            }
        """

        self.__generate_log_dfs()
        for key, df in self._log_dfs.items():
            # Convert dataframe to JSON string
            json_data = df.to_json(orient="records", indent=2)

            filename = f"{key}.json"
            self.jsons.append({
                "filename": filename,
                "data": json_data,
                "key": key
            })

    def __generate_log_dfs(self):
        """
        Constructs pandas DataFrames for all parsed log categories.

        This method consolidates all event lists into a structured dictionary
        of DataFrames for downstream processing or export.
        """
        self._log_dfs = {
            "reps": pd.DataFrame(self.all_reps),
            "neut": pd.DataFrame(self.all_neuts),
            "dmg": pd.DataFrame(self.all_dmg),
            "nos": pd.DataFrame(self.all_nos),
            "matches": pd.DataFrame(self.matches),
            "cap_warnings": pd.DataFrame(self.all_cap_warnings),
            "cap_reps":pd.DataFrame(),
            "scrams": pd.DataFrame(self.all_scrams),
            "jams": pd.DataFrame(self.all_jams),
            "drones": pd.DataFrame(self.all_drones),
            "links": pd.DataFrame(self.all_links),
            "reloads": pd.DataFrame(self.all_reloads),
            "skipped": pd.DataFrame(self.all_skipped)
        }
