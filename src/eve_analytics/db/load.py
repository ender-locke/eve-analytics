def insert_logs(rows):
    sql = """
          INSERT INTO combat_data (
              id, log_type_id, action_to, action_from,
              action_timestamp, module, amount,
              hit_quality, create_ts, update_ts, retired
          ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) \
          """

    values = [
        (
            r.get("id"),
            r.get("log_type_id"),
            r.get("action_to"),
            r.get("action_from"),
            r.get("action_timestamp"),
            r.get("module"),
            r.get("amount"),
            r.get("hit_quality"),
            r.get("create_ts"),
            r.get("update_ts"),
            int(r.get("retired", False))
        )
        for r in rows if r is not None
    ]

    cursor.executemany(sql, values)
    conn.commit()