import sqlite3
from pathlib import Path
from eve_analytics.db.schema.schemas import *
from eve_analytics.data.logs import log_types, keys_to_remove
from datetime import datetime, timezone
import uuid

class Database:

    def __init__(self, ea, db_path=None):
        self.ea = ea
        if db_path is None:
            base = Path.home() / ".eveanalytics"
            base.mkdir(exist_ok=True)
            self.db_path = base / "combat_logs.db"
        else:
            self.db_path = db_path

        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self.cursor = self.conn.cursor()
        self.create_tables = [
            create_combat_data_sql,
            create_combat_log_types_sql,
            create_matches_sql,
            create_pilot_bridge_sql,
            create_users_sql,
            create_invgroups_sql,
            create_dmgtypeattribs_sql,
            create_invcategories_sql,
            create_invtypes_sql
        ]
        self._build_schema()

    def insert_combat_logs(self):
        now = datetime.now(timezone.utc).isoformat()
        sql = """
              INSERT INTO combat_data (
                  id, match_id, pilot, action_timestamp,
                  amount, action_to, action_from, direction,
                  module, log_type_id, hit_quality,
                  ship, corp_tag, og_line, cleaned_line,
                  create_ts, update_ts, retired
              ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) \
              """
        rows = []

        rows.extend([self.process_json_record(log) for log in self.ea.parsed_logs.all_cap_warnings])
        rows.extend([self.process_json_record(log) for log in self.ea.parsed_logs.all_cap_reps])
        rows.extend([self.process_json_record(log) for log in self.ea.parsed_logs.all_dmg])
        rows.extend([self.process_json_record(log) for log in self.ea.parsed_logs.all_drones])
        rows.extend([self.process_json_record(log) for log in self.ea.parsed_logs.all_jams])
        rows.extend([self.process_json_record(log) for log in self.ea.parsed_logs.all_links])
        rows.extend([self.process_json_record(log) for log in self.ea.parsed_logs.all_neuts])
        rows.extend([self.process_json_record(log) for log in self.ea.parsed_logs.all_nos])
        rows.extend([self.process_json_record(log) for log in self.ea.parsed_logs.all_reloads])
        rows.extend([self.process_json_record(log) for log in self.ea.parsed_logs.all_reps])
        rows.extend([self.process_json_record(log) for log in self.ea.parsed_logs.all_scrams])

        values = [
            (
                r.get("id"),
                r.get("match_id"),
                r.get("pilot"),
                r.get("action_timestamp"),
                r.get("amount"),
                r.get("action_to"),
                r.get("action_from"),
                r.get("direction"),
                r.get("module"),
                r.get("log_type_id"),
                r.get("hit_quality"),
                r.get("ship"),
                r.get("corp_tag", ""),
                r.get("og_line"),
                r.get("cleaned_line"),
                r.get("create_ts", now),
                r.get("update_ts", now),
                int(r.get("retired", False))
            )
            for r in rows if r
        ]

        self.cursor.executemany(sql, values)
        self.conn.commit()

    # -------------------------
    # Utility
    # -------------------------
    def convert_ms_to_timestamp(self, value):
        if isinstance(value, datetime):
            return value.isoformat()

        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value / 1000, tz=timezone.utc).isoformat()

        return None

    def process_json_record(self, record):
        record["id"] = str(uuid.uuid4())

        record['log_type_id'] = self.get_log_type_id(this_type=record['row_type'])

        if "to" in record:
            record['action_to'] = record['to'] if record['to'] else "unknown"
        else:
            record['action_to'] = 'unknown'

        if "from" in record:
            record['action_from'] = record['from'] if record['from'] else "unknown"
        else:
            record['action_from'] = "unknown"

        if "time" in record:
            record["action_timestamp"] = self.convert_ms_to_timestamp(record["time"])

        record["create_ts"] = datetime.now(timezone.utc).isoformat()
        record["update_ts"] = datetime.now(timezone.utc).isoformat()
        record['retired'] = False

        if "module" in record and record["module"] is not None:
            if not isinstance(record["module"], str):
                record["module"] = str(record["module"])

        for key in keys_to_remove:
            record.pop(key, None)

        return record

    def get_log_type_id(self, this_type):
        """
        all_types: list of dicts, each with 'id' and 'name'
        this_type: string to match against the 'name' field
        Returns: matching id or None if not found
        """
        if this_type == "dmg":
            this_type = "damage"

        for t in log_types:
            if t.get("name") == this_type:
                return t.get("id")
        return 0

    def _build_schema(self):
        for sql in self.create_tables:
            print(sql)
            self.cursor.execute(sql)
        self.conn.commit()

    def close(self):
        self.conn.close()