from datetime import timedelta

TOLERANCE = timedelta(seconds=15)

def get_match_id(timestamp, matches):
    """
    Given a timestamp and a list of match dicts with start, end, id,
    return the id of the match the timestamp falls inside.
    """
    for m in matches:
        if (m["start"] - TOLERANCE) <= timestamp <= (m["end"] + TOLERANCE):
            return m["id"]
    return "unknown"
