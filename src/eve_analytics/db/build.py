import sqlite3
from pathlib import Path
from eve_analytics.db.schema.schemas import *

def create_db_dir():
    HOME = Path.home()
    DATA_DIR = HOME / ".eveanalytics"
    DATA_DIR.mkdir(exist_ok=True)
    return DATA_DIR / "eve_analytics.db"

def init_db():
    db_path = create_db_dir()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    tables = [
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

    for sql in tables:
        cursor.execute(sql)

    conn.commit()
    conn.close()