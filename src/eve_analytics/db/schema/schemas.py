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
    ship TEXT,
    corp_tag TEXT,
    og_line TEXT,
    cleaned_line TEXT,
    create_ts TEXT,
    update_ts TEXT,
    retired INTEGER
 )
"""

create_combat_log_types_sql = """
 CREATE TABLE IF NOT EXISTS combat_log_types (
        id TEXT PRIMARY KEY,
        name TEXT,
        description TEXT,
        create_ts TEXT,
        update_ts TEXT,
        retired INTEGER
 ) ;
 insert or ignore into combat_log_types
VALUES
    (8, 'drones', 'drones', '2025-12-10 23:00:02.241799 UTC', '2025-12-10 23:00:02.241799 UTC', 0),
    (2, 'reps', 'reps', '2025-12-10 23:00:02.241799 UTC', '2025-12-10 23:00:02.241799 UTC', 0),
    (6, 'nos', 'nos', '2025-12-10 23:00:02.241799 UTC', '2025-12-10 23:00:02.241799 UTC', 0),
    (4, 'jams', 'jams', '2025-12-10 23:00:02.241799 UTC', '2025-12-10 23:00:02.241799 UTC', 0),
    (5, 'scrams', 'scrams', '2025-12-10 23:00:02.241799 UTC', '2025-12-10 23:00:02.241799 UTC', 0),
    (1, 'damage', 'damage', '2025-12-10 23:00:02.241799 UTC', '2025-12-10 23:00:02.241799 UTC', 0),
    (3, 'links', 'links', '2025-12-10 23:00:02.241799 UTC', '2025-12-10 23:00:02.241799 UTC', 0),
    (9, 'reloads', 'reloads', '2025-12-10 23:00:02.241799 UTC', '2025-12-10 23:00:02.241799 UTC', 0),
    (7, 'neuts', 'neuts', '2025-12-10 23:00:02.241799 UTC', '2026-01-13 05:27:13.795662 UTC', 0),
    (10, 'cap warning', 'cap warnings', '2026-01-18 06:16:06.503523 UTC', '2026-01-18 06:16:06.503523 UTC', 0),
    (11, 'cap reps', 'cap reps', '2026-04-03 04:41:04.539993 UTC', '2026-04-03 04:41:04.539993 UTC', 0)
"""

create_matches_sql = """
CREATE TABLE IF NOT EXISTS matches (
      id TEXT PRIMARY KEY,
      description TEXT,
      countdown_start_ts TEXT,
      match_start_ts TEXT,
      match_end_ts TEXT,
      create_ts TEXT,
      update_ts TEXT,
      retired INTEGER
) 
"""

create_pilot_bridge_sql = """
CREATE TABLE IF NOT EXISTS pilot_to_match_to_ship_bridge (
      pilot_id INTEGER,
      match_id TEXT,
      ship_id INTGER,
      create_ts TEXT,
      update_ts TEXT,
      retired INTEGER,
      PRIMARY KEY (pilot_id, match_id, ship_id)
    ) 
"""

create_users_sql = """
CREATE TABLE IF NOT EXISTS users (
       id INTEGER PRIMARY KEY,
        character_name TEXT,
       last_login TEXT,
       create_ts TEXT,
       update_ts TEXT,
       retired INTEGER
) \
"""

create_invtypes_sql = """
CREATE TABLE if not exists invtypes (
    typeId INTEGER PRIMARY KEY,
    raceId INTEGER,
    metaGroupId INTEGER,
    marketGroupID INTEGER,
    typeName TEXT,
    mass FLOAT,
     groupId INTEGER,
    create_ts TEXT,
    update_ts TEXT,
    retired INTEGER
) 
"""

create_invgroups_sql = """
CREATE TABLE IF NOT EXISTS invgroups (
      groupId INTEGER PRIMARY KEY,
      name TEXT,
      categoryId INTEGER,
      create_ts TEXT,
      update_ts TEXT,
      retired INTEGER
) 
"""

create_invcategories_sql = """
CREATE TABLE IF NOT EXISTS invcategories (
    categoryId INTEGER PRIMARY KEY,
    name TEXT,
    create_ts TEXT,
    update_ts TEXT,
    retired INTEGER
)  """

create_dmgtypeattribs_sql = """
CREATE TABLE IF NOT EXISTS dmgtypeattribs (
    value FLOAT,
    typeId INTEGER,
    attributeId INTEGER,
    create_ts TEXT,
    update_ts TEXT,
    retired INTEGER,
    PRIMARY KEY(value, typeId, attributeId)
)  """
