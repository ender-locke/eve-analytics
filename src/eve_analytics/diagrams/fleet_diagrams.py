from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from .helpers.icons import get_eve_icon, add_icon_legend, add_bg_leg
import matplotlib.dates as mdates
from .helpers.pilots import is_involving_pilot
from .helpers.math import compute_ema
from matplotlib.lines import Line2D
from pathlib import Path
import matplotlib.pyplot as plt
from datetime import timedelta
from collections import defaultdict
from PIL import Image
import numpy as np
import random
from datetime import datetime

illegal_color = (0.3, 0, 0, 0.3)   # dark red with 30% opacity
LEFT = 0.15
RIGHT = 0.94
Y_IMG = 0.08
Y_TEXT = 0.15
Y_DMG = 0.045   # raw damage
Y_DPS = 0.025   # dps
alpha = 0.15
BASE_DIR = Path(__file__).resolve().parent
skull_img_loc = BASE_DIR / "imgs" / "skull_logo.png"

skull_img = np.array(Image.open(skull_img_loc).convert("RGBA"))

def generate_fleet_diagrams(
        diagram_type,
        unique_pilots,
        matches,
        damage_df,
        drone_list,
        reload_list,
        first_actions_list,
        pilot_dmg,
        pilot_dmg_taken,
        fleet_dmg,
        fleet_reps,
        pilot_deaths,
        fleet_jams,
        ctx,
        pilots_ships
):
    """
    Generates fleet-level combat diagrams for one or more matches.

    This function produces time-series visualizations of fleet activity,
    including DPS, reps, pilot actions, and key combat events. Diagrams
    can be generated in either offensive or defensive mode.

    Features:
    - Per-pilot DPS (smoothed via EMA)
    - Fleet-wide DPS and repair trends
    - Drone damage (separate dashed lines)
    - First-action markers per pilot
    - Reload and drone engagement icons (offensive mode)
    - Pilot death markers
    - Fleet composition display (ships, pilots, and stats)
    - Match timeline segmentation (minute markers and countdown phase)

    Args:
        diagram_type (str): Type of diagram to generate.
            Supported values:
            - "offensive": outgoing damage and actions
            - "defensive": incoming damage and fleet reps

        unique_pilots (list[str]): List of pilot names in the match.

        matches (list[dict]): Match metadata objects, each containing:
            - id (str): Match ID
            - start (str): Match start timestamp
            - end (str): Match end timestamp
            - cd_start (str): Countdown start timestamp
            - description (str, optional): Match label

        damage_df (list[dict]): Damage events with rolling DPS values.

        drone_list (list[dict]): Drone engagement events.

        reload_list (list[dict]): Reload events.

        first_actions_list (list[dict]): First action timestamps per pilot.

        pilot_dmg (list[dict]): Outgoing damage statistics per pilot.

        pilot_dmg_taken (list[dict]): Incoming damage statistics per pilot.

        fleet_dmg (list[dict]): Fleet-level rolling DPS data.

        fleet_reps (list[dict]): Fleet-level rolling repair data.

        pilot_deaths (list[dict]): Pilot death events with timestamps.

        fleet_jams (list[dict]): ECM/jamming events.

        ctx (FlightContext): Context object containing:
            - configuration flags
            - icon assets (reload, drones, etc.)
            - query parameters

        pilots_ships (dict[str, list]): Mapping of pilots to their ships.
            Each entry contains ship metadata including:
            - ship ID
            - ship name
            - mass
            - class

    Returns:
        list[dict]: List of generated diagram objects, where each entry contains:
            - "fig" (matplotlib.figure.Figure): The generated figure
            - "name" (str): Suggested filename for saving the figure

    Notes:
        - Uses exponential moving average (EMA) smoothing for DPS and reps.
        - Timestamps are expected in ISO or '%Y-%m-%d %H:%M:%S' format.
        - Diagram styling is optimized for dark backgrounds.
        - Behavior is influenced by flags in the provided FlightContext.
    """
    is_offensive = diagram_type == "offensive"
    is_defensive = diagram_type == "defensive"
    dmg_direction = "incoming" if is_defensive else "outgoing"

    dmg_stats = pilot_dmg if is_offensive else pilot_dmg_taken

    figures = []

    dmg_hp_max = defaultdict(int)
    reps_hp_max = defaultdict(int)

    dmg_hp_max[dmg_direction] = 0
    reps_hp_max[dmg_direction] = 0

    for match in matches:
        start = match["start"]
        start_dt = datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
        cd_start = datetime.strptime(match['cd_start'], "%Y-%m-%d %H:%M:%S")
        end = match["end"]
        end_dt = datetime.strptime(end, "%Y-%m-%d %H:%M:%S")
        this_match_id = match['id']
        match_minutes = int((end_dt - start_dt).total_seconds() // 60) + 1
        label = match.get("description", f"Match {this_match_id}")

        pilot_dmg_output = defaultdict(dict)

        for dmg in dmg_stats:
            if dmg['match_id'] == this_match_id:
                pilot_dmg_output[dmg['pilot']] = dmg

        reload_x = 95
        jam_x = 35
        death_x = 70
        drone_engage_x = 10
        n = random.uniform(25, 30)

        match_first_actions = []
        for action in first_actions_list:
            if action['match_id'] == this_match_id:
                match_first_actions.append({
                    "pilot": action['pilot'],
                    "ts": action["action_timestamp"]
                })

        fig, ax_hp = plt.subplots(figsize=(14, 8))
        ax_x2 = ax_hp.twinx()

        ax_hp.xaxis_date()
        ax_x2.xaxis_date()

        ax_hp.relim()
        ax_hp.autoscale_view()

        ax_x2.relim()
        ax_x2.autoscale_view()

        fig.subplots_adjust(bottom=0.23)

        ax_hp.set_facecolor("#0c0c1a")  # deep space navy
        fig.patch.set_facecolor("#0c0c1a")  # figure background
        colors = iter(plt.cm.tab10.colors)

        match_comp = []
        for pilot in pilots_ships:
            for (pilot_name, ship_id, ship, match_id, ship_class, ship_mass) in pilots_ships[pilot]:
                if match_id == match['id']:
                    match_comp.append({
                        "name": ship if ship else "",
                        "id": ship_id,
                        "pilot": pilot_name,
                        "mass": ship_mass if ship_mass else 0,
                        "img": get_eve_icon(ctx.icons["base"], ship_id, ship)
                    })

        match_comp = sorted(
            match_comp,
            key=lambda s: (s.get("name").lower(), s["pilot"].lower())
        )

        fleet_reps_by_ts = defaultdict(float)
        for pilot in unique_pilots:
            color = next(colors)

            pilot_reloads = []
            pilot_drone_engagements = []
            pilot_jammed = []

            df = damage_df.copy()

            pilot_mask = (
                df["pilot"].eq(pilot)
            )

            base_mask = (
                    (df["ts_sec"] >= cd_start) &
                    (df["ts_sec"] <= end_dt) &
                    pilot_mask
            )

            dmg_mask = (
                    base_mask &
                    df["is_drone"].eq(False)
            )

            drone_mask = (
                    base_mask &
                    (df["is_drone"].eq(True))
            )

            dps_by_ts = (
                df.loc[dmg_mask]
                .groupby("ts_sec")["rolling_dps"]
                .sum()
                .sort_index()
            )

            drone_dps_by_ts = (
                df.loc[drone_mask]
                .groupby("ts_sec")["rolling_dps"]
                .sum()
                .sort_index()
            )

            if is_offensive:
                # todo add in when we got jams/ incoming jams
                for e in fleet_jams:
                    action_ts = datetime.strptime(e["action_timestamp"], '%Y-%m-%d %H:%M:%S')
                    if (
                            cd_start <= action_ts <= end_dt
                            and is_involving_pilot(e, pilot)
                            and e["direction"] == "outgoing"
                    ):
                        pilot_jammed.append(action_ts)

                # get reloads
                for e in reload_list:
                    action_ts = datetime.strptime(e["action_timestamp"].replace("T", " "), '%Y-%m-%d %H:%M:%S')

                    if (
                        cd_start <= action_ts <= end_dt
                        and is_involving_pilot(e, pilot)
                    ):
                        pilot_reloads.append(action_ts)

                # get drone engagementsf
                for e in drone_list:
                    action_ts = datetime.strptime(e["action_timestamp"].replace("T", " "), '%Y-%m-%d %H:%M:%S')

                    if (
                        cd_start <= action_ts <= end_dt
                        and is_involving_pilot(e, pilot)
                    ):
                        pilot_drone_engagements.append(action_ts)

            if is_offensive:
                # todo add in when we got jams/ incoming jams
                for e in fleet_jams:
                    action_ts = datetime.strptime(e["action_timestamp"], '%Y-%m-%d %H:%M:%S')
                    if (
                            cd_start <= action_ts <= end_dt
                            and is_involving_pilot(e, pilot)
                            and e["direction"] == "incoming"
                    ):
                        pilot_jammed.append(action_ts)

                for reload in pilot_reloads:
                    img = OffsetImage(ctx.reload_img, zoom=.5)
                    ab = AnnotationBbox(img, (reload, reload_x), frameon=False, zorder=500, clip_on=True)
                    ax_x2.add_artist(ab)

                reload_x -= 5

                # todo map out jams here
                #for jam in pilot_jammed:
                #    img = OffsetImage(ctx.jam_img, zoom=.5)
                #    ab = AnnotationBbox(img, (jam, jam_x), frameon=False, zorder=500)
                #    ax_x2.add_artist(ab)

                for drone in pilot_drone_engagements:
                    img = OffsetImage(ctx.drone_img, zoom=.5)
                    ab = AnnotationBbox(img, (drone, drone_engage_x), frameon=False, zorder=500, clip_on=True)
                    ax_x2.add_artist(ab)

                drone_engage_x += 5

            # add in first actions for this pilot
            this_pilots_first_action = []
            for first_actions in match_first_actions:
                if first_actions['pilot'] == pilot:
                    this_pilots_first_action.append(first_actions.get('ts'))

            ts_sorted = dps_by_ts.index.to_list()
            dps_values = dps_by_ts.values

            dps_ems = compute_ema(dps_values, alpha)

            drones_sorted = drone_dps_by_ts.index.to_list()
            drone_values = drone_dps_by_ts.values

            drone_ems = compute_ema(drone_values, alpha)

            ts_sorted = [datetime.fromisoformat(str(t)) for t in ts_sorted]
            drones_sorted = [datetime.fromisoformat(str(t)) for t in drones_sorted]

            ax_hp.plot(
                ts_sorted,
                dps_ems,
                label=f"{pilot}",
                color=color,
                linestyle="-",
                linewidth=2.5,
                alpha=0.95
            )

            # Drones DPS — dashed
            ax_hp.plot(
                drones_sorted,
                drone_ems,
                color=color,
                linestyle="--",
                linewidth=2.0,
                alpha=0.85
            )

            for first_action in this_pilots_first_action:
                ax_x2.scatter(
                    [first_action],
                    [n],
                    marker="o",
                    s=100,
                    color=color,
                    label=f"{pilot} FA"
                )
                n -= 5

        if is_defensive:
            for e in fleet_reps:
                action_ts = datetime.strptime(e["action_timestamp"].replace("T", " "), '%Y-%m-%d %H:%M:%S')
                if cd_start <= action_ts <= end_dt and e["direction"] == "incoming":
                    fleet_reps_by_ts[action_ts] += e["rolling_reps"]
                    reps_hp_max[dmg_direction] = max(reps_hp_max[dmg_direction], e["rolling_reps"], fleet_reps_by_ts[action_ts])

            fleet_reps_sorted = sorted(fleet_reps_by_ts.keys())
            fleet_reps_values = [fleet_reps_by_ts[ts] for ts in fleet_reps_sorted]

            ema = compute_ema(fleet_reps_values, alpha)

            # plot fleet reps
            ax_hp.plot(
                fleet_reps_sorted,
                ema,
                label=f"Fl33t Reps",
                color="#44AA99",
                linestyle="-",
                linewidth=2.5,
                alpha=0.95
            )

        fleet_mask = (
                (fleet_dmg["ts_sec"] >= cd_start) &
                (fleet_dmg["ts_sec"] <= end_dt) &
                (fleet_dmg["direction"].isin([
                    dmg_direction,
                    f"{dmg_direction}-breacher-pods",
                    f"{dmg_direction}-drones",
                ]))
        )

        filtered = fleet_dmg.loc[fleet_mask]

        fleet_dps_by_ts = (
            filtered.groupby("ts_sec")["rolling_dps"]
            .sum()
        )

        hp_max = max(
            filtered["rolling_dps"].max(),
            fleet_dps_by_ts.max(),
            dmg_hp_max[dmg_direction]
        )

        fleet_dps_sorted = sorted(fleet_dps_by_ts.keys())
        fleet_dps_values = [fleet_dps_by_ts[ts] for ts in fleet_dps_sorted]

        ema = compute_ema(fleet_dps_values, alpha)

        death_plots = []
        for death in pilot_deaths:
            if death['seconds_before_match_end'] > 10 and death['match_id'] == this_match_id:
                death_plots.append(death['last_action_ts'])

        for death_ts in death_plots:
            img = OffsetImage(skull_img, zoom=.03)
            ab = AnnotationBbox(img, (death_ts, death_x), frameon=False, zorder=500, annotation_clip=True, clip_on=True)
            ab.set_clip_on(True)
            ax_x2.add_artist(ab)

        # plot fleet dps
        ax_hp.plot(
            fleet_dps_sorted,
            ema,
            label=f"Fl33t DPS",
            color="#CC6677",
            linestyle="-",
            linewidth=2.5,
            alpha=0.95
        )

        ax_hp.set_xlim(cd_start, end_dt)
        ax_x2.set_xlim(cd_start, end_dt)

        #ax_hp.set_ylim(0, (max(hp_max, reps_hp_max[dmg_direction]) * 1.1))
        #ax_x2.set_ylim(0, 100)

        ax_hp.tick_params(colors="white")
        ax_x2.tick_params(axis="y", labelright=False)

        ax_hp.set_xlabel("Time (Eve)", color="white")
        ax_hp.set_ylabel("HP (Damage)", color="white")

        ax_hp.set_title(f"Fleet Diagram: {dmg_direction.capitalize()} | {label}", color="white", pad=20)

        handles, labels = ax_hp.get_legend_handles_labels()

        custom_lines = [
            Line2D([0], [0], linestyle="--", label="Drone Damage"),
            Line2D([0], [0], linestyle="-", label="Ship Damage"),
        ]

        handles.extend(custom_lines)

        legend = ax_hp.legend(
            handles=handles,
            loc="upper right",
            facecolor="#1a1a2e",
            edgecolor="white",
            labelcolor="white"
        )
        legend.set_zorder(1000)

        # order the axis correctly so lines show above icons
        ax_x2.set_zorder(1)
        ax_hp.set_zorder(2)
        ax_hp.patch.set_visible(False)

        if is_offensive:
            # adding in second leg for icons
            add_bg_leg(ax_hp)
            add_icon_legend(
                ax_hp,
                {
                    "Reload": ctx.reload_img,
                    "Drones Engaged": ctx.drone_img,
                    #"Jams": ctx.jam_img
                },
                start_x=0.86,
                start_y=0.09
            )

        for i in range(match_minutes):
            x = start_dt + timedelta(minutes=i)

            ax_x2.axvline(
                x,
                color="white",
                linestyle=":",   # '--', ':', '-.', etc.
                alpha=0.25,
                linewidth=3
            )

            ax_x2.text(
                x,
                1.01,                # slightly above the plot
                str(i),
                transform=ax_x2.get_xaxis_transform(),
                ha="center",
                va="bottom",
                color="white",
                fontsize=8,
                alpha=0.85
            )

        ax_hp.grid(True, linestyle='--', alpha=0.3, color="white")

        ax_hp.axvspan(cd_start, start_dt, facecolor=illegal_color, edgecolor=None)

        BUFFER = 0.03  # space between ships
        x = LEFT  # starting point

        match_comp.sort(key=lambda x: x["mass"], reverse=True)

        for ship in match_comp:
            if ship.get("ship", None):
                ship_img = ship["img"]
                if ship_img.any():
                    # Ship image
                    ship_box = OffsetImage(ship_img, zoom=1.1)
                    ship_box.set_alpha(0.95)
                else:
                    blank = np.zeros((10, 10, 4))
                    ship_box = OffsetImage(blank, zoom=1.1)

                ship_ab = AnnotationBbox(
                    ship_box,
                    (x, Y_IMG),
                    xycoords=fig.transFigure,
                    frameon=False,
                    box_alignment=(0.5, 0.5),
                    zorder=5,
                    clip_on=True
                )
                fig.add_artist(ship_ab)

                # Pilot name above
                fig.text(
                    x,
                    Y_TEXT,
                    ship["pilot"],
                    ha="center",
                    va="bottom",
                    fontsize=9,
                    color="white",
                    alpha=0.9
                )

                stats = pilot_dmg_output[ship["pilot"]]
                if stats:
                    box_style = dict(
                        boxstyle="round,pad=0.35",
                        facecolor="#0c0c1a",   # match background
                        edgecolor="#2e2e5e",     # subtle white border
                        linewidth=0.8,
                        alpha=0.9
                    )

                    dps = stats.get("dps")

                    if dps is None:
                        dps_label = "0.00 DPS"
                    else:
                        dps_label = f"{dps:.2f} DPS"

                    combined_text = (
                        f"{int(stats['total_damage']):,} Raw\n"
                        f"{dps_label}"
                    )

                    fig.text(
                        x,
                        Y_DMG,
                        combined_text,
                        ha="center",
                        va="top",
                        fontsize=8,
                        color="white",
                        zorder=10,
                        bbox=box_style
                    )

                x += 0.05 + BUFFER

        figures.append({
            "fig": fig,
            "name": f"{dmg_direction} dps fleet diagram {label}_v1.2",
        })

    return figures
