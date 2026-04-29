from eve_analytics.ingest.splicer import parse_combat_log
from eve_analytics.ingest.matches import parse_match_intervals
from eve_analytics.exceptions.file_errors import MissingFilesError
from eve_analytics.classes.json_log_data import JSONLogData
from eve_analytics.data.logs import log_keys
import hashlib
from datetime import timedelta, timezone
import pandas as pd


class ParsedLogs:

    def __init__(self, folder):
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

        :return:
        """

        return f"<ParsedLogs> {self.folder} | logs parsed -> {self.logs_parsed}"

    @property
    def log_dfs(self):
        return self._log_dfs

    def __set_files(self):
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
        match_intervals = parse_match_intervals(self.local_log)
        matches = []
        for idx, (start, end,) in enumerate(match_intervals):
            match_num = idx + 1
            matches.append({
                "idx": match_num,
                "id": hashlib.sha256(f"{start}:{end}".encode()).hexdigest(),
                "start": start,
                "end": end,
                "description": f"match {match_num}",
                "add_row": True
            })

        self.matches = matches
        self.export_date = matches[0]['start']

    def __to_utc(self, dt):
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)  # assume it's UTC
        return dt.astimezone(timezone.utc)

    def __get_match_id(self, ts):
        timestamp = self.__to_utc(ts)
        TOLERANCE = timedelta(seconds=15)

        for m in self.matches:
            start = self.__to_utc(m["start"])
            end = self.__to_utc(m["end"])

            if (start - TOLERANCE) <= timestamp <= (end + TOLERANCE):
                return m["id"]

        return "unknown"


    def __parse_combat_logs(self):
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
        self.__generate_log_dfs()

    def generate_jsons(self):
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
        if there's nothing here just re run it

        :return:
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
