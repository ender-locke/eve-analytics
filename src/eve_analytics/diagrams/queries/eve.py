
def get_drones(db):
    """
    Runs the Drone types query against BigQuery and returns results as a list of dicts.
    """
    query = """
            SELECT
                it.typeName
            FROM invtypes it
             JOIN invgroups ig
                  ON it.groupID = ig.groupID
             JOIN invcategories ic
                  ON ig.categoryID = ic.categoryID
            WHERE ic.name = 'Drone'
            ORDER BY it.typeName 
            """

    rows = db.cursor.execute(query).fetchall() # could be execute

    return [row.typeName for row in rows]


def get_damage_output_stats(db, match_id, direction="outgoing"):
    query = """
            SELECT
                cd.pilot,
                cd.match_id,
                SUM(cd.amount) AS total_damage,
                MIN(cd.action_timestamp) AS min_ts,
                MAX(cd.action_timestamp) AS max_ts,
                (strftime('%s', MAX(cd.action_timestamp)) - strftime('%s', MIN(cd.action_timestamp))) AS duration_seconds,
                ROUND(
                        SUM(cd.amount) * 1.0 /
                        NULLIF((strftime('%s', MAX(cd.action_timestamp)) - strftime('%s', MIN(cd.action_timestamp))), 0),
                        2
                ) AS dps
            FROM combat_data cd
            WHERE cd.log_type_id = 1
              AND cd.direction LIKE ?
              AND cd.match_id = ?
            GROUP BY cd.pilot, cd.match_id \
            """

    params = (f"{direction}%", match_id)

    rows = db.cursor.execute(query, params).fetchall()

    return rows

def get_first_actions(db, match_id):
    query = """
            SELECT action_timestamp, pilot, match_id
            FROM (
                     SELECT
                         cd.action_timestamp,
                         cd.pilot,
                         cd.match_id,
                         ROW_NUMBER() OVER (
                    PARTITION BY cd.match_id, cd.pilot
                    ORDER BY cd.action_timestamp
                ) AS rn
                     FROM combat_data cd
                     WHERE cd.log_type_id NOT IN (3, 10)
                       AND cd.direction = 'outgoing'
                       AND cd.match_id = ?
                 ) t
            WHERE rn = 1
            ORDER BY match_id, pilot \
            """

    rows = db.cursor.execute(query, (match_id,)).fetchall()

    return rows

def get_log_data(db, log_type: str, match_id):
    query = """
            SELECT
                cd.match_id,
                cd.pilot,
                cd.action_timestamp,
                cd.amount,
                cd.action_to,
                cd.action_from,
                cd.direction,
                clt.name
            FROM combat_data cd
                     LEFT JOIN combat_log_types clt
                               ON cd.log_type_id = clt.id
            WHERE clt.name = ?
              AND cd.match_id = ? \
            """

    params = (log_type, match_id)

    rows = db.cursor.execute(query, params).fetchall()

    return rows

def get_matches(db, start_date, end_date):
    query = """
            SELECT
                m.match_start_ts AS start,
                m.match_end_ts AS end,
            m.id,
            m.description
            FROM matches m
            WHERE m.match_start_ts <= ?
              AND m.match_end_ts >= ?
              AND m.retired = 0 \
            """

    params = (end_date, start_date)

    rows = db.cursor.execute(query, params).fetchall()

    return rows

def get_unique_pilots(db, match_id):
    query = """
            SELECT cd.pilot
            FROM combat_data cd
            WHERE cd.match_id = ?
            GROUP BY cd.pilot 
            """

    rows = db.cursor.execute(query, (match_id,)).fetchall()

    return [row["pilot"] for row in rows]


def get_pilots_and_ships(db, match_id):
    query = """
            SELECT
                cd.pilot,
                pms.ship_id,
                inv.typeName,
                cd.match_id,
                ig.name,
                inv.mass AS ship_mass
            FROM combat_data cd
             LEFT JOIN users u
                       ON cd.pilot = u.character_name
             LEFT JOIN pilot_to_match_to_ship_bridge pms
                       ON cd.match_id = pms.match_id
                           AND u.id = pms.pilot_id
             LEFT JOIN invtypes inv
                       ON pms.ship_id = inv.typeID
             LEFT JOIN invgroups ig
                       ON inv.groupID = ig.groupID
            WHERE cd.match_id = ?
            GROUP BY
                cd.pilot,
                pms.ship_id,
                inv.typeName,
                cd.match_id,
                ig.name,
                ta.value
            ORDER BY
                ta.value,
                cd.pilot ASC,
                inv.typeName ASC 
            """

    rows = db.cursor.execute(query, (match_id,)).fetchall()

    return rows

def get_fleet_rolling_dps(db, seconds, match_id):
    query = """
            WITH filtered AS (
                SELECT
                    cd.match_id,
                    cd.direction,
                    cd.amount,
                    strftime('%s', cd.action_timestamp) AS ts_sec,
                    (LOWER(cd.module) LIKE '%breacher pod%') AS is_breacher_pod,
                    clt.name
                FROM combat_data cd
                         LEFT JOIN combat_log_types clt
                                   ON cd.log_type_id = clt.id
                WHERE cd.amount IS NOT NULL
                  AND clt.name = 'damage'
                  AND cd.match_id = ?
            )

            SELECT
                f1.match_id,
                f1.direction,
                datetime(f1.ts_sec, 'unixepoch') AS action_timestamp,
                f1.is_breacher_pod,

                SUM(f2.amount) * 1.0 / ? AS rolling_dps

            FROM filtered f1
             JOIN filtered f2
                  ON f1.match_id = f2.match_id
                      AND f1.direction = f2.direction
                      AND f1.is_breacher_pod = f2.is_breacher_pod
                      AND f2.ts_sec BETWEEN (f1.ts_sec - ?) AND f1.ts_sec

            GROUP BY
                f1.match_id,
                f1.direction,
                f1.ts_sec,
                f1.is_breacher_pod

            ORDER BY f1.ts_sec; \
            """

    params = (match_id, seconds, seconds)

    return db.cursor.execute(query, params).fetchall()


def get_rolling_dps_w_pilots(db, seconds):
    query = """
            WITH all_drones AS (
                SELECT it.typeName
                FROM invtypes it
                         JOIN invgroups ig ON it.groupID = ig.groupID
                         JOIN invcategories ic ON ig.categoryID = ic.categoryID
                WHERE ic.name = 'Drone'
            ),

                 normalized_damage AS (
                     SELECT
                         cd.match_id,
                         cd.action_from AS "from",
                         cd.action_to AS "to",
                         cd.direction,
                         cd.amount AS damage,
                         strftime('%s', cd.action_timestamp) AS ts_sec,
                         cd.action_timestamp AS ts,
                         (ad.typeName IS NOT NULL) AS is_drone
                     FROM combat_data cd
                              LEFT JOIN combat_log_types clt
                                        ON clt.id = cd.log_type_id
                              LEFT JOIN all_drones ad
                                        ON LOWER(cd.module) = LOWER(ad.typeName)
                     WHERE cd.amount IS NOT NULL
                       AND clt.name = 'damage'
                 )

            SELECT
                f1.match_id,
                f1."from",
                f1."to",
                f1.direction,
                f1.ts AS action_timestamp,
                f1.is_drone,

                SUM(f2.damage) * 1.0 / ? AS rolling_dps

            FROM normalized_damage f1
                     JOIN normalized_damage f2
                          ON f1.match_id = f2.match_id
                              AND f1."from" = f2."from"
                              AND f1."to" = f2."to"
                              AND f1.direction = f2.direction
                              AND f1.is_drone = f2.is_drone
                              AND f2.ts_sec BETWEEN (f1.ts_sec - ?) AND f1.ts_sec

            GROUP BY
                f1.match_id,
                f1."from",
                f1."to",
                f1.direction,
                f1.ts_sec,
                f1.is_drone

            ORDER BY f1.ts_sec; \
            """

    params = (seconds, seconds)

    return db.cursor.execute(query, params).fetchall()


def get_rolling_dps_bp(db, seconds, match_id):
    query = """
            WITH all_drones AS (
                SELECT it.typeName
                FROM invtypes it
                         JOIN invgroups ig ON it.groupID = ig.groupID
                         JOIN invcategories ic ON ig.categoryID = ic.categoryID
                WHERE ic.name = 'Drone'
            ),

                 normalized_damage AS (
                     SELECT
                         cd.match_id,
                         cd.amount AS damage,
                         strftime('%s', cd.action_timestamp) AS ts_sec,
                         cd.action_timestamp AS ts,

                         CASE
                             WHEN cd.direction = 'incoming' THEN cd.action_to
                             ELSE cd.action_from
                             END AS pilot,

                         cd.direction,
                         (ad.typeName IS NOT NULL) AS is_drone,
                         (LOWER(cd.module) LIKE '%breacher pod%') AS is_breacher_pod

                     FROM combat_data cd
                              LEFT JOIN combat_log_types clt
                                        ON clt.id = cd.log_type_id
                              LEFT JOIN all_drones ad
                                        ON LOWER(cd.module) = LOWER(ad.typeName)

                     WHERE cd.amount IS NOT NULL
                       AND clt.name = 'damage'
                       AND cd.match_id = ?
                 )

            SELECT
                f1.match_id,
                f1.direction,
                f1.pilot,
                datetime(f1.ts_sec, 'unixepoch') AS action_timestamp,
                f1.is_drone,
                f1.is_breacher_pod,

                SUM(f2.damage) * 1.0 / ? AS rolling_dps

            FROM normalized_damage f1
                     JOIN normalized_damage f2
                          ON f1.match_id = f2.match_id
                              AND f1.pilot = f2.pilot
                              AND f1.direction = f2.direction
                              AND f1.is_drone = f2.is_drone
                              AND f1.is_breacher_pod = f2.is_breacher_pod
                              AND f2.ts_sec BETWEEN (f1.ts_sec - ?) AND f1.ts_sec

            GROUP BY
                f1.match_id,
                f1.direction,
                f1.pilot,
                f1.ts_sec,
                f1.is_drone,
                f1.is_breacher_pod

            ORDER BY f1.ts_sec; \
            """

    params = (match_id, seconds, seconds)

    return db.cursor.execute(query, params).fetchall()

def get_fleet_rolling_reps(db, seconds, match_id):
    """
    SQLite version of rolling reps calculation.
    """

    seconds = seconds - 1

    query = """
            WITH all_drones AS (
                SELECT it.typeName
                FROM invtypes it
                         JOIN invgroups ig ON it.groupID = ig.groupID
                         JOIN invcategories ic ON ig.categoryID = ic.categoryID
                WHERE ic.name = 'Drone'
            ),

                 normalized_damage AS (
                     SELECT
                         cd.match_id,
                         cd.action_timestamp AS ts,
                         CAST(strftime('%s', cd.action_timestamp) AS INTEGER) AS ts_sec,
                         cd.direction,
                         CASE WHEN ad.typeName IS NOT NULL THEN 1 ELSE 0 END AS is_drone,
                         CASE WHEN lower(cd.module) LIKE '%breacher pod%' THEN 1 ELSE 0 END AS is_breacher_pod,
                         SUM(cd.amount) AS rep_amount
                     FROM combat_data cd
                              LEFT JOIN combat_log_types clt
                                        ON clt.id = cd.log_type_id
                              LEFT JOIN all_drones ad
                                        ON lower(cd.module) = lower(ad.typeName)
                     WHERE cd.amount IS NOT NULL
                       AND clt.name = 'reps'
                       AND cd.match_id = :match_id
                     GROUP BY
                         cd.match_id,
                         ts,
                         ts_sec,
                         cd.direction,
                         is_drone,
                         is_breacher_pod
                 )

            SELECT
                match_id,
                direction,
                ts AS action_timestamp,
                is_drone,
                is_breacher_pod,
                SUM(rep_amount) OVER (
            PARTITION BY match_id, direction, is_drone, is_breacher_pod
            ORDER BY ts_sec
            ROWS BETWEEN :seconds PRECEDING AND CURRENT ROW
        ) * 1.0 / :seconds AS rolling_reps
            FROM normalized_damage
            ORDER BY ts, match_id, direction; \
            """

    params = {
        "match_id": match_id,
        "seconds": seconds
    }

    return db.cursor.execute(query, params).fetchall()

def get_match_last_action_by_pilot(db, match_id):
    """
    SQLite version: last action per pilot for a single match_id.
    """

    query = """
            SELECT
                cd.pilot,
                cd.match_id,
                MAX(cd.action_timestamp) AS last_action_ts,
                MAX(m.match_end_ts) AS match_end_ts,
                (
                    CAST(strftime('%s', MAX(m.match_end_ts)) AS INTEGER)
                        -
                    CAST(strftime('%s', MAX(cd.action_timestamp)) AS INTEGER)
                    ) AS seconds_before_match_end
            FROM combat_data cd
                     LEFT JOIN matches m
                               ON cd.match_id = m.id
            WHERE cd.match_id = ?
              AND cd.action_timestamp <= m.match_end_ts
            GROUP BY cd.match_id, cd.pilot
            ORDER BY last_action_ts DESC \
            """

    return db.cursor.execute(query, (match_id, )).fetchall()


