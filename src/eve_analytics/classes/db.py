import sqlite3
from pathlib import Path
from eve_analytics.exceptions.db_errors import MissingSDEError
from eve_analytics.db.schema.schemas import *
from eve_analytics.data.logs import log_types, keys_to_remove
from eve_analytics.data.eve_sde import sde_url
from datetime import datetime, timezone
import hashlib
import shutil
import os
import wget
import yaml
import zipfile

class Database:

    def __init__(self, ea, db_path=None):
        self.ea = ea
        self.sde_location = None
        if db_path is None:
            self.base = Path.home() / ".eveanalytics"
            self.base.mkdir(exist_ok=True)
            self.db_path = self.base / "combat_logs.db"
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

    def __repr__(self) -> str:
        """

        :return:
        """

        return f"<Database> | {self.db_path}"

    def default_db_load(self):
        self.__insert_matches()
        self.__insert_combat_logs()
        self.__load_eve_data()

    def __insert_matches(self):
        now = datetime.now(timezone.utc).isoformat()
        sql = """
            INSERT OR IGNORE INTO matches (
                id, description, match_start_ts,
                match_end_ts,
                create_ts, update_ts, retired
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        values = [
            (
                r.get("id", 0),
                r.get('description', ""),
                r.get('start'),
                r.get('end'),
                r.get("create_ts", now),
                r.get("update_ts", now),
                int(r.get("retired", False))
            )
            for r in self.ea.parsed_logs.matches if r
        ]

        self.cursor.executemany(sql, values)
        self.conn.commit()

    def __insert_combat_logs(self):
        now = datetime.now(timezone.utc).isoformat()
        sql = """
              INSERT OR IGNORE INTO combat_data (
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
        raw = f"{record['action_timestamp']}:{record['pilot']}:{record['direction']}:{record['log_type_id']}:{record['cleaned_line']}".encode()
        record["id"] = hashlib.sha256(raw).hexdigest()

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
            for statement in sql.split(';'):
                self.cursor.execute(statement)
        self.conn.commit()


    def _download_sde_zip(self):
        zip_path = f"{self.base}/sde.zip"
        unzip_path = f"{self.base}/sde"

        try:
            if os.path.isfile(zip_path):
                os.unlink(zip_path)

            if os.path.isdir(unzip_path):
                shutil.rmtree(unzip_path)

        except Exception as e:
            print(f"Cleanup error: {e}")

        wget.download(sde_url, str(zip_path))
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(unzip_path)

        self.sde_location = unzip_path

    def __load_eve_data(self):
        self._load_sde_data()

    def _load_sde_data(self):
        self._download_sde_zip()
        if self.sde_location is None:
            raise MissingSDEError(location=self.base)

        self._load_invtypes()
        self._load_invcategories()
        self._load_invgroups()

    def _load_invtypes(self):
        with open(f'{self.sde_location}/types.yaml', 'rb') as f:
            types_data = yaml.load(f, Loader=yaml.CSafeLoader)

            now = datetime.now(timezone.utc).isoformat()
            inv_list = []
            for key, value in types_data.items():
                type_id = key
                mass = value.get("mass", 0)
                group_id = value.get('groupId', 0)
                type_name = value['name'].get('en')
                race_id = value.get('raceId', 0)
                meta_group_id = value.get("metaGroupId", 0)
                market_group_id = value.get("marketGroupId", 0)
                inv_list.append({
                    'group_id': group_id,
                    'type_id': type_id,
                    'race_id': race_id,
                    'mass': mass,
                    'meta_group_id': meta_group_id,
                    'market_group_id': market_group_id,
                    'type_name': type_name,
                    'create_ts': now,
                    'update_ts': now,
                    'retired': False
                })

        self.inv_values = inv_list
        self._insert_invtypes()

    def _insert_invtypes(self):
        now = datetime.now(timezone.utc).isoformat()
        sql = """
              INSERT OR IGNORE INTO invtypes (
                  typeId, raceId, metaGroupId,
                  marketGroupId, typeName, 
                  mass, groupId,
                  create_ts, update_ts, retired
              ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) \
              """

        values = [
            (
                r.get("type_id"),
                r.get('race_id', 0),
                r.get("meta_group_id", 0),
                r.get("market_group_id", 0),
                r.get("type_name", ""),
                r.get("mass", 0),
                r.get("group_id"),
                r.get("create_ts", now),
                r.get("update_ts", now),
                int(r.get("retired", False))
            )
            for r in self.inv_values if r
        ]

        #self.cursor.executemany(sql, values)
        for v in values:
            try:
                self.cursor.execute(sql, v)
            except Exception as e:
                print("FAILED ROW:", v)
                print("ERROR:", e)
                break
                self.conn.commit()

    def _load_invcategories(self):
        with open(f'{self.sde_location}/categories.yaml', 'r') as f:
            cat_data = yaml.safe_load(f)
            category_list = []
            now = datetime.now(timezone.utc).isoformat()
            for key, value in cat_data.items():
                category_id = key
                name_en = value['name']['en']
                category_list.append({
                    'category_id': category_id,
                    'name': name_en,
                    'create_ts': now,
                    'update_ts': now,
                    'retired': False
                })
        self.category_values = category_list
        self._insert_invcategories()

    def _insert_invcategories(self):
        now = datetime.now(timezone.utc).isoformat()
        sql = """
              INSERT OR IGNORE INTO invcategories (
                  categoryId, name,
                  create_ts, update_ts, retired
              ) VALUES (?, ?, ?, ?, ?)
              """

        values = [
            (
                r.get("category_id", 0),
                r.get('name_en', ""),
                r.get("create_ts", now),
                r.get("update_ts", now),
                int(r.get("retired", False))
            )
            for r in self.category_values if r
        ]

        self.cursor.executemany(sql, values)
        self.conn.commit()

    def _load_invgroups(self):
        with open(f'{self.sde_location}/groups.yaml', 'r') as f:
            groups_data = yaml.safe_load(f)
            now = datetime.now(timezone.utc).isoformat()
            group_list = []
            for key, value in groups_data.items():
                category_id = value.get('categoryId', 0)
                name_en = value['name'].get('en')
                group_id = key
                group_list.append({
                    'group_id': group_id,
                    'category_id': category_id,
                    'name': name_en,
                    'create_ts': now,
                    'update_ts': now,
                    'retired': False
                })
        self.group_values = group_list
        self._insert_invgroups()

    def _insert_invgroups(self):
        now = datetime.now(timezone.utc).isoformat()
        sql = """
              INSERT OR IGNORE INTO invgroups (
                  groupId, name, categoryId,
                  create_ts, update_ts, retired
              ) VALUES (?, ?, ?, ?, ?, ?)
              """

        values = [
            (
                r.get("group_id", 0),
                r.get('name_en', ""),
                r.get("category_id", 0),
                r.get("create_ts", now),
                r.get("update_ts", now),
                int(r.get("retired", False))
            )
            for r in self.group_values if r
        ]

        self.cursor.executemany(sql, values)
        self.conn.commit()

    def execute(self, sql, params=None):
        return self.cursor.execute(sql, params).fetchall()

    def close(self):
        self.conn.close()