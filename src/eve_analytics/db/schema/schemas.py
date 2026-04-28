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

create_combat_log_types_sql = """
 CREATE TABLE IF NOT EXISTS combat_log_types (
        id TEXT PRIMARY KEY,
        name TEXT,
        description TEXT.
        create_ts TEXT,
        update_ts TEXT,
        retired INTEGER
 ) 
"""

create_matches_sql = """
CREATE TABLE IF NOT EXISTS matches (
      id TEXT PRIMARY KEY,
      description TEXT.
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
       id INTEGER PRIMARY_KEY,
        character_name TEXT,
       last_login TEXT,
       create_ts TEXT,
       update_ts TEXT,
       retired INTEGER
) \
"""

create_invtypes_sql = """
CREATE TABLE IF NOT EXISTS invtypes (
    typeId INTEGER PRIMARY_KEY,
    typeName TEXT,
     groupId INTEGER,
    create_ts TEXT,
    update_ts TEXT,
    retired INTEGER
) 
"""


create_invgroups_sql = """
CREATE TABLE IF NOT EXISTS invgroups (
      groupId INTEGER PRIMARY_KEY,
      name TEXT,
      categoryId INTEGER,
      create_ts TEXT,
      update_ts TEXT,
      retired INTEGER
) 
"""

create_invcategories_sql = """
CREATE TABLE IF NOT EXISTS invcategories (
    categoryId INTEGER PRIMARY_KEY,
    name TEXT,
    categoryId INTEGER,
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
    retired INTEGER
    PRIMARY_KEY(value, typeId, attributeId)
)  """
