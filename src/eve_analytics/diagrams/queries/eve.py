from google.cloud import bigquery

def get_drones():
    """
    Runs the Drone types query against BigQuery and returns results as a list of dicts.
    """
    client = bigquery.Client()

    query = """
            SELECT
                it.typeName,
            FROM `sde.invtypes` it
                     JOIN `sde.invgroups` ig
                          ON it.groupID = ig.groupID
                     JOIN `sde.invcategories` ic
                          ON ig.categoryID = ic.categoryID
            WHERE ic.name = 'Drone'
            ORDER BY it.typeName 
            """

    rows = client.query(query).result()

    return [row.typeName for row in rows]


def get_damage_output_stats(match_ids, direction="outgoing"):
    client = bigquery.Client()
    dmg_query = """
                SELECT
                    cd.pilot,
                    cd.match_id,
                    SUM(cd.amount) AS total_damage,
                    MIN(cd.action_timestamp) AS min_ts,
                    MAX(cd.action_timestamp) AS max_ts,
                    TIMESTAMP_DIFF(
                            MAX(cd.action_timestamp),
                            MIN(cd.action_timestamp),
                        SECOND
    ) AS duration_seconds,
            ROUND(
                SAFE_DIVIDE(
                        SUM(cd.amount),
                        TIMESTAMP_DIFF(
                                MAX(cd.action_timestamp),
                                MIN(cd.action_timestamp),
                            SECOND
            )
                ),
                            2) AS dps
                FROM `combat_logs.combat_data` cd
                WHERE cd.log_type_id = 1
                  AND cd.direction like CONCAT(@direction, "%")
                  AND cd.match_id IN unnest(@match_ids)
                GROUP BY cd.pilot, cd.match_id 

                """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ArrayQueryParameter(
                "match_ids", "STRING", match_ids
            ),
            bigquery.ScalarQueryParameter(
                "direction", "STRING", direction
            ),
        ]
    )

    rows = client.query(dmg_query, job_config=job_config).result()

    return list(rows)


def get_first_actions(match_ids):
    client = bigquery.Client()
    actions_query = """
        SELECT *
        FROM (
         SELECT
             cd.action_timestamp,
             cd.pilot,
             cd.match_id,
             ROW_NUMBER() OVER (
        PARTITION BY cd.match_id, cd.pilot
        ORDER BY cd.action_timestamp
        ) AS rn
        FROM `combat_logs.combat_data` cd
         WHERE cd.log_type_id NOT IN (3, 10)
            AND cd.direction = "outgoing"
             ) t
        WHERE rn = 1
          and match_id in unnest(@match_ids)
        ORDER BY match_id, pilot
            
        """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ArrayQueryParameter(
                "match_ids", "STRING", match_ids
            ),
        ]
    )

    rows = client.query(actions_query, job_config=job_config).result()

    return list(rows)



def get_log_data(log_type: str, match_ids):
    client = bigquery.Client()

    log_query = """
        select cd.match_id, cd.pilot, cd.action_timestamp,
           cd.amount, cd.action_to, cd.action_from, cd.direction,
           clt.name
        from combat_logs.combat_data cd
        left join combat_logs.combat_log_types clt
            on cd.log_type_id = clt.id
        where clt.name = @log_type
            and cd.match_id in unnest(@match_ids)
        """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter(
                "log_type", "STRING", log_type
            ),
            bigquery.ArrayQueryParameter(
                "match_ids", "STRING", match_ids
            ),
        ]
    )

    rows = client.query(log_query, job_config=job_config).result()

    return list(rows)


def get_matches(start_date, end_date):
    client = bigquery.Client()

    match_query = """
      SELECT
          m.match_start_ts AS start,
          m.match_end_ts AS `end`,
          m.id,
          m.description
      FROM matches.matches m
      WHERE m.match_start_ts <= @end_date
        AND m.match_end_ts >= @start_date
        AND m.retired = false 
      """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("start_date", "TIMESTAMP", start_date),
            bigquery.ScalarQueryParameter("end_date", "TIMESTAMP", end_date),
        ]
    )

    rows = client.query(match_query, job_config=job_config).result()

    return list(rows)

def get_unique_pilots(match_ids):
    client = bigquery.Client()

    pilot_query = """
      select cd.pilot,
      from combat_logs.combat_data cd
      where cd.match_id in unnest(@match_ids)
      group by cd.pilot
    
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ArrayQueryParameter(
                "match_ids", "STRING", match_ids
            ),
        ]
    )

    rows = client.query(pilot_query, job_config=job_config).result()

    return [row for row in rows]


def get_pilots_and_ships(match_ids):
    client = bigquery.Client()

    pilot_query = """
      select cd.pilot, pms.ship_id, inv.typeName, cd.match_id, ig.name, ta.value as ship_mass
      from combat_logs.combat_data cd
               left join users.users u
                         on cd.pilot = u.character_name
               left join matches.pilot_to_match_to_ship_bridge pms
                         on cd.match_id = pms.match_id
                             and u.id = pms.pilot_id
               left join sde.invtypes inv
                         on pms.ship_id = inv.typeID
               left join sde.invgroups ig
                         on inv.groupID = ig.groupID
               left join sde.dgmtypeattribs ta
                         on inv.typeID = ta.typeID
                             and ta.attributeID = 4
      where cd.match_id in unnest(@match_ids)
      group by cd.pilot, pms.ship_id, inv.typeName, cd.match_id, ig.name, ta.value
      order by ta.value, cd.pilot asc, inv.typeName asc
          """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ArrayQueryParameter(
                "match_ids", "STRING", match_ids
            ),
        ]
    )

    rows = client.query(pilot_query, job_config=job_config).result()

    return [row for row in rows]

def get_fleet_rolling_dps(seconds, match_ids):

    client = bigquery.Client()
    seconds = seconds - 1

    query = """
            WITH all_drones AS (
                SELECT it.typeName
                FROM `sde.invtypes` it
                         JOIN `sde.invgroups` ig
                              ON it.groupID = ig.groupID
                         JOIN `sde.invcategories` ic
                              ON ig.categoryID = ic.categoryID
                WHERE ic.name = 'Drone'
            ),

-- 1 Raw damage normalized to 1-second buckets
                 normalized_damage AS (
                     SELECT
                         cd.match_id,
                         TIMESTAMP_SECONDS(UNIX_SECONDS(cd.action_timestamp)) AS ts,
                         UNIX_SECONDS(cd.action_timestamp) AS ts_sec,
                         cd.direction,
                         ad.typeName IS NOT NULL AS is_drone,
                         CONTAINS_SUBSTR(LOWER(cd.module), "breacher pod") AS is_breacher_pod,
                         SUM(cd.amount) AS damage
                     FROM `combat_logs.combat_data` cd
                              LEFT JOIN combat_logs.combat_log_types clt
                                        ON clt.id = cd.log_type_id
                              LEFT JOIN all_drones ad
                                        ON LOWER(cd.module) = LOWER(ad.typeName)
                     WHERE cd.amount IS NOT NULL
                       AND clt.name = "damage"
                       AND cd.match_id IN UNNEST(@match_ids)
            GROUP BY
                cd.match_id,
                ts,
                ts_sec,
                cd.direction,
                is_drone,
                is_breacher_pod
                ),

-- 2 Get min/max second per partition
                bounds AS (
            SELECT
                match_id,
                direction,
                is_drone,
                is_breacher_pod,
                MIN(ts_sec) AS min_sec,
                MAX(ts_sec) AS max_sec
            FROM normalized_damage
            GROUP BY match_id, direction, is_drone, is_breacher_pod
                ),

-- 3 Generate full second grid
                second_grid AS (
            SELECT
                b.match_id,
                b.direction,
                b.is_drone,
                b.is_breacher_pod,
                sec AS ts_sec,
                TIMESTAMP_SECONDS(sec) AS ts
            FROM bounds b,
                UNNEST(GENERATE_ARRAY(b.min_sec, b.max_sec)) AS sec
                ),

-- 4 Left join damage onto full second grid
                filled_seconds AS (
            SELECT
                g.match_id,
                g.direction,
                g.is_drone,
                g.is_breacher_pod,
                g.ts,
                g.ts_sec,
                IFNULL(n.damage, 0) AS damage
            FROM second_grid g
                LEFT JOIN normalized_damage n
            ON g.match_id = n.match_id
                AND g.direction = n.direction
                AND g.is_drone = n.is_drone
                AND g.is_breacher_pod = n.is_breacher_pod
                AND g.ts_sec = n.ts_sec
                )

-- 5 Rolling DPS over true N seconds
            SELECT
                match_id,
                direction,
                ts AS action_timestamp,
                is_drone,
                is_breacher_pod,
                SUM(damage) OVER (
        PARTITION BY match_id, direction, is_drone, is_breacher_pod
        ORDER BY ts_sec
        ROWS BETWEEN @seconds PRECEDING AND CURRENT ROW
    ) / CAST(@seconds AS FLOAT64) AS rolling_dps
            FROM filled_seconds
            ORDER BY ts, match_id, direction;

            """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("seconds", "INT64", seconds),
            bigquery.ArrayQueryParameter(
                "match_ids", "STRING", match_ids
            ),
        ]
    )

    rows = client.query(query, job_config=job_config).result()

    return list(rows)


def get_rolling_dps_w_pilots(seconds):

    client = bigquery.Client()

    query = """
            WITH all_drones as (
                SELECT
                    it.typeName,
                FROM `sde.invtypes` it
                         JOIN `sde.invgroups` ig
                              ON it.groupID = ig.groupID
                         JOIN `sde.invcategories` ic
                              ON ig.categoryID = ic.categoryID
                WHERE ic.name = 'Drone'
                ORDER BY it.typeName
            ),

                 normalized_damage AS (
                     SELECT
                         cd.match_id,
                         cd.action_timestamp AS ts,
                         UNIX_SECONDS(cd.action_timestamp) AS ts_sec,
                         cd.action_from AS `from`,
                         cd.action_to   AS `to`,
                         cd.direction,
                         cd.amount AS damage,
                         ad.typeName IS NOT NULL AS is_drone
                     FROM `combat_logs.combat_data` cd
                              LEFT JOIN combat_logs.combat_log_types clt
                                        ON clt.id = cd.log_type_id
                              LEFT JOIN all_drones ad
                                        ON LOWER(cd.module) = LOWER(ad.typeName)
                     WHERE cd.amount IS NOT NULL
                       AND clt.name = "damage"
                 )

            SELECT
                match_id,
                `from`,
                `to`,
                direction,
                ts AS action_timestamp,
                is_drone,
                SUM(damage) OVER (
    PARTITION BY match_id, `from`, `to`, direction, is_drone
    ORDER BY ts_sec
    RANGE BETWEEN @seconds PRECEDING AND CURRENT ROW
    ) / CAST(@seconds AS FLOAT64) AS rolling_dps
            FROM normalized_damage
            ORDER BY ts asc, match_id, `from`, `to`, direction
            """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("seconds", "INT64", seconds)
        ]
    )

    rows = client.query(query, job_config=job_config).result()

    return list(rows)


def get_rolling_dps_bp(seconds, match_ids):
    client = bigquery.Client()
    seconds = seconds - 1
    query = """
            WITH all_drones AS (
                SELECT it.typeName
                FROM `sde.invtypes` it
                         JOIN `sde.invgroups` ig
                              ON it.groupID = ig.groupID
                         JOIN `sde.invcategories` ic
                              ON ig.categoryID = ic.categoryID
                WHERE ic.name = 'Drone'
            ),

-- 1 Raw damage normalized to 1-second buckets
                 normalized_damage AS (
                     SELECT
                         cd.match_id,
                         TIMESTAMP_SECONDS(UNIX_SECONDS(cd.action_timestamp)) AS ts,
                         UNIX_SECONDS(cd.action_timestamp) AS ts_sec,
                         cd.direction,
                         ad.typeName IS NOT NULL AS is_drone,
                         CONTAINS_SUBSTR(LOWER(cd.module), "breacher pod") AS is_breacher_pod,
                         SUM(cd.amount) AS damage,
                         case when cd.direction = "incoming" then
                                  cd.action_to
                              else
                                  cd.action_from end as pilot,
                     FROM `combat_logs.combat_data` cd
                              LEFT JOIN combat_logs.combat_log_types clt
                                        ON clt.id = cd.log_type_id
                              LEFT JOIN all_drones ad
                                        ON LOWER(cd.module) = LOWER(ad.typeName)
                     WHERE cd.amount IS NOT NULL
                       AND clt.name = "damage"
                       AND cd.match_id IN UNNEST(@match_ids)
            GROUP BY
                cd.match_id,
                ts,
                pilot,
                ts_sec,
                cd.direction,
                is_drone,
                is_breacher_pod
                ),

-- 2 Get min/max second per partition
                bounds AS (
            SELECT
                match_id,
                pilot,
                direction,
                is_drone,
                is_breacher_pod,
                MIN(ts_sec) AS min_sec,
                MAX(ts_sec) AS max_sec
            FROM normalized_damage
            GROUP BY match_id, direction, is_drone, is_breacher_pod, pilot
                ),

-- 3 Generate full second grid
                second_grid AS (
            SELECT
                b.match_id,
                b.direction,
                b,pilot,
                b.is_drone,
                b.is_breacher_pod,
                sec AS ts_sec,
                TIMESTAMP_SECONDS(sec) AS ts
            FROM bounds b,
                UNNEST(GENERATE_ARRAY(b.min_sec, b.max_sec)) AS sec
                ),

-- 4 Left join damage onto full second grid
                filled_seconds AS (
            SELECT
                g.match_id,
                g.direction,
                g.is_drone,
                g.pilot,
                g.is_breacher_pod,
                g.ts,
                g.ts_sec,
                IFNULL(n.damage, 0) AS damage
            FROM second_grid g
                LEFT JOIN normalized_damage n
            ON g.match_id = n.match_id
                AND g.direction = n.direction
                AND g.is_drone = n.is_drone
                AND g.is_breacher_pod = n.is_breacher_pod
                AND g.ts_sec = n.ts_sec
                AND g.pilot = n.pilot
                )

-- 5 Rolling DPS over true N seconds
            SELECT
                match_id,
                direction,
                pilot,
                ts AS action_timestamp,
                is_drone,
                is_breacher_pod,
                SUM(damage) OVER (
        PARTITION BY match_id, direction, pilot, is_drone, is_breacher_pod
        ORDER BY ts_sec
        ROWS BETWEEN @seconds PRECEDING AND CURRENT ROW
    ) / CAST(@seconds AS FLOAT64) AS rolling_dps
            FROM filled_seconds
            ORDER BY ts, match_id, direction;
            """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter(
                "seconds", "INT64", seconds
            ),
            bigquery.ArrayQueryParameter(
                "match_ids", "STRING", match_ids
            ),
        ],
    )

    rows = client.query(query, job_config=job_config).result()

    return list(rows)

def get_fleet_rolling_reps(seconds, match_ids):

    client = bigquery.Client()
    seconds = seconds - 1

    query = """
            WITH all_drones AS (
                SELECT it.typeName
                FROM `sde.invtypes` it
                         JOIN `sde.invgroups` ig
                              ON it.groupID = ig.groupID
                         JOIN `sde.invcategories` ic
                              ON ig.categoryID = ic.categoryID
                WHERE ic.name = 'Drone'
            ),

-- 1 Raw damage normalized to 1-second buckets
                 normalized_damage AS (
                     SELECT
                         cd.match_id,
                         TIMESTAMP_SECONDS(UNIX_SECONDS(cd.action_timestamp)) AS ts,
                         UNIX_SECONDS(cd.action_timestamp) AS ts_sec,
                         cd.direction,
                         ad.typeName IS NOT NULL AS is_drone,
                         CONTAINS_SUBSTR(LOWER(cd.module), "breacher pod") AS is_breacher_pod,
                         SUM(cd.amount) AS rep_amount
                     FROM `combat_logs.combat_data` cd
                              LEFT JOIN combat_logs.combat_log_types clt
                                        ON clt.id = cd.log_type_id
                              LEFT JOIN all_drones ad
                                        ON LOWER(cd.module) = LOWER(ad.typeName)
                     WHERE cd.amount IS NOT NULL
                       AND clt.name = "reps"
                       AND cd.match_id IN UNNEST(@match_ids)
            GROUP BY
                cd.match_id,
                ts,
                ts_sec,
                cd.direction,
                is_drone,
                is_breacher_pod
                ),

-- 2 Get min/max second per partition
                bounds AS (
            SELECT
                match_id,
                direction,
                is_drone,
                is_breacher_pod,
                MIN(ts_sec) AS min_sec,
                MAX(ts_sec) AS max_sec
            FROM normalized_damage
            GROUP BY match_id, direction, is_drone, is_breacher_pod
                ),

-- 3 Generate full second grid
                second_grid AS (
            SELECT
                b.match_id,
                b.direction,
                b.is_drone,
                b.is_breacher_pod,
                sec AS ts_sec,
                TIMESTAMP_SECONDS(sec) AS ts
            FROM bounds b,
                UNNEST(GENERATE_ARRAY(b.min_sec, b.max_sec)) AS sec
                ),

-- 4 Left join damage onto full second grid
                filled_seconds AS (
            SELECT
                g.match_id,
                g.direction,
                g.is_drone,
                g.is_breacher_pod,
                g.ts,
                g.ts_sec,
                IFNULL(n.rep_amount, 0) AS rep_amount
            FROM second_grid g
                LEFT JOIN normalized_damage n
            ON g.match_id = n.match_id
                AND g.direction = n.direction
                AND g.is_drone = n.is_drone
                AND g.is_breacher_pod = n.is_breacher_pod
                AND g.ts_sec = n.ts_sec
                )

-- 5 Rolling DPS over true N seconds
            SELECT
                match_id,
                direction,
                ts AS action_timestamp,
                is_drone,
                is_breacher_pod,
                SUM(rep_amount) OVER (
        PARTITION BY match_id, direction, is_drone, is_breacher_pod
        ORDER BY ts_sec
        ROWS BETWEEN @seconds PRECEDING AND CURRENT ROW
    ) / CAST(@seconds AS FLOAT64) AS rolling_reps
            FROM filled_seconds
            ORDER BY ts, match_id, direction;

            """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("seconds", "INT64", seconds),
            bigquery.ArrayQueryParameter(
                "match_ids", "STRING", match_ids
            ),
        ]
    )

    rows = client.query(query, job_config=job_config).result()

    return list(rows)


def get_match_last_action_by_pilot(match_ids):
    client = bigquery.Client()
    actions_query = f"""
        SELECT
            cd.pilot,
            m.id as match_id,
            MAX(cd.action_timestamp) AS last_action_ts,
            ANY_VALUE(m.match_end_ts) AS match_end_ts,
            TIMESTAMP_DIFF(
                ANY_VALUE(m.match_end_ts),
                MAX(cd.action_timestamp),
                SECOND
            ) AS seconds_before_match_end
        FROM `combat_logs.combat_data` cd
        LEFT JOIN `matches.matches` m
          ON cd.match_id = m.id
        WHERE cd.match_id in Unnest(@match_ids)
          AND cd.action_timestamp <= m.match_end_ts
        GROUP BY cd.match_id, cd.pilot, m.id
        ORDER BY cd.match_id, last_action_ts DESC
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ArrayQueryParameter(
                "match_ids", "STRING", match_ids
            ),
        ]
    )

    rows = client.query(actions_query, job_config=job_config).result()

    return list(rows)

