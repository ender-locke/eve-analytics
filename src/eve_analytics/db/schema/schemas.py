create_combat_data_sql = """
 CREATE TABLE IF NOT EXISTS combat_data (
    id TEXT PRIMARY KEY,
    match_id TEXT, 
    pilot TEXT,
    action_timestamp TEXT,
    amount REAL,
    action_to TEXT,
    action_from TEXT,
    direction TEXT,
     module TEXT,
    log_type_id INTEGER,
    hit_quality TEXT,
    ship TEXT.
    corp_tag TEXT.
    og_line TEXT.
    cleaned_line TEXT,
    create_ts TEXT,
    update_ts TEXT,
    retired INTEGER
 )
"""

create_combat_data_sql = """
 CREATE TABLE IF NOT EXISTS combat_data (
        id TEXT PRIMARY KEY,
        log_type_id INTEGER,
        action_to TEXT,
        action_from TEXT,
        action_timestamp TEXT,
        module TEXT,
        amount REAL,
        hit_quality TEXT,
        create_ts TEXT,
        update_ts TEXT,
        retired INTEGER
 ) \
 """
