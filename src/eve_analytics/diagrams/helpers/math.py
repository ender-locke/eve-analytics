from collections import defaultdict


def compute_ema(values, alpha):
    ema = []
    for i, v in enumerate(values):
        if i == 0:
            ema.append(v)
        else:
            ema.append(alpha * v + (1 - alpha) * ema[i-1])
    return ema

def compute_ema_logic(values, alpha, ts_name="action_timestamp", amount_key="amount"):
    by_ts = defaultdict(float)

    for v in values:
        ts = v[ts_name]
        by_ts[ts] += v[amount_key]

    ts_values = sorted(by_ts.keys())
    vals = [by_ts[ts] for ts in ts_values]

    ema = []
    for i, v in enumerate(vals):
        if i == 0:
            ema.append(v)
        else:
            ema.append(alpha * v + (1 - alpha) * ema[i-1])
    return ema, ts_values



