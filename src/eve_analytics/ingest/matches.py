import re
from datetime import datetime


def parse_match_intervals(local_path):
    lines = local_path.read_text(encoding="utf-16-le").splitlines()

    session_ranges = []
    current_start = None
    line_re = re.compile(r'\[ ([\d.:\s]+) \] .*?>\s*(.+)', re.IGNORECASE)

    for line in lines:
        match = line_re.search(line)
        if not match:
            continue
        timestamp_str, message = match.groups()
        timestamp = datetime.strptime(timestamp_str.strip(), "%Y.%m.%d %H:%M:%S")
        message_lower = message.strip().lower()

        if message_lower in {"go", "gooo", "0", "goo", "goooo", "googogo", "gogogo!"}:
            current_start = timestamp
        elif current_start and any(k in message_lower for k in ("gf", "wf", "gg", "time", "match completed!")):
            session_ranges.append((current_start, timestamp))
            current_start = None

    return session_ranges
