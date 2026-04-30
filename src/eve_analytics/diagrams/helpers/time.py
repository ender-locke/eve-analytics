from datetime import datetime

def parse_ts(ts):
    return datetime.strptime(ts.replace("T", " "), '%Y-%m-%d %H:%M:%S')
