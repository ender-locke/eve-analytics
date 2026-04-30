
def get_match_timestamps(db, match_id):
    """
    """
    query = """
            SELECT
                m.match_start_ts,
                m.match_end_ts,
                m.countdown_start_ts
            FROM matches m
            WHERE m.id = ?
            """

    rows = db.cursor.execute(query, (match_id,)).fetchall() # could be execute

    return rows
