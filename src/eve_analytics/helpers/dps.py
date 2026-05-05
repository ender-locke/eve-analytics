import pandas as pd


def fleet_rolling(df, drone_names, match_id, seconds):
    seconds = seconds - 1

    df = df[
        (df["match_id"] == match_id) &
        (df["amount"].notna()) &
        (df["log_type"] == "damage")
        ].copy()

    df["is_drone"] = df["module"].str.lower().isin(
        {d.lower() for d in drone_names}
    )
    df["is_breacher_pod"] = df["module"].str.lower().str.contains("breacher pod")

    df["ts"] = pd.to_datetime(df["action_timestamp"])
    df["ts_sec"] = df["ts"].dt.floor("s")

    grouped = (
        df.groupby([
            "match_id",
            "direction",
            "is_drone",
            "is_breacher_pod",
            "ts_sec"
        ])["amount"]
        .sum()
        .reset_index(name="damage")
    )

    def fill_group(group):
        full_range = pd.date_range(
            group["ts_sec"].min(),
            group["ts_sec"].max(),
            freq="S"
        )
        return (
            group.set_index("ts_sec")
            .reindex(full_range, fill_value=0)
            .rename_axis("ts_sec")
            .reset_index()
        )

    filled = (
        grouped.groupby(
            ["match_id", "direction", "is_drone", "is_breacher_pod"],
            group_keys=False
        )
        .apply(lambda g: fill_group(g).assign(
            match_id=g.name[0],
            direction=g.name[1],
            is_drone=g.name[2],
            is_breacher_pod=g.name[3],
        ))
    )

    filled = filled.sort_values("ts_sec")

    filled["rolling_dps"] = (
            filled.groupby([
                "match_id",
                "direction",
                "is_drone",
                "is_breacher_pod"
            ])["damage"]
            .rolling(window=seconds + 1, min_periods=1)
            .sum()
            .reset_index(level=[0,1,2,3], drop=True)
            / float(seconds)
    )

    return filled
