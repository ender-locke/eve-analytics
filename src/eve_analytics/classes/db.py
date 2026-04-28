import sqlite3
from pathlib import Path
from eve_analytics.db.schema.schemas import *
from datetime import datetime, timezone

class Database:

    def __init__(self, db_path=None):
        if db_path is None:
            base = Path.home() / ".eveanalytics"
            base.mkdir(exist_ok=True)
            self.db_path = base / "combat_logs.db"
        else:
            self.db_path = db_path

        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self.cursor = self.conn.cursor()
        self._build_schema()
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

    def _build_schema(self):
        for sql in self.create_tables:
            self.cursor.execute(sql)
        self.conn.commit()

    def close(self):
        self.conn.close()