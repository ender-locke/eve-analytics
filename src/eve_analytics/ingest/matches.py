import re
from datetime import datetime


def parse_match_intervals(local_path):
    """
    Extract match start and end time intervals from a local log file.

    This function scans a UTF-16 LE encoded log file for textual cues that
    indicate the beginning and end of a match. It identifies "start" events
    based on common trigger phrases (e.g., "go", "gogogo") and "end" events
    based on completion phrases (e.g., "gf", "gg", "match completed!").

    Parameters
    ----------
    local_path : pathlib.Path
        Path to the log file containing match-related messages.

    Returns
    -------
    list[tuple[datetime, datetime]]
        A list of (start_timestamp, end_timestamp) tuples representing
        detected match intervals.

    Notes
    -----
    - The file is expected to be encoded as UTF-16 LE.
    - Start triggers include variations of "go" (e.g., "gooo", "gogogo").
    - End triggers include phrases like "gf", "gg", "wf", "time",
      and "match completed!".
    - If a start trigger is found without a corresponding end trigger,
      it is ignored.
    - Matching is case-insensitive and based on simple keyword detection,
      so false positives are possible depending on log content.

    Raises
    ------
    IOError
        If the file cannot be read.
    ValueError
        If a timestamp cannot be parsed due to unexpected format.
    """
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
