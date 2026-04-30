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
        damage_list,
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
    is_offensive = diagram_type == "offensive"
    is_defensive = diagram_type == "defensive"
    dmg_direction = "incoming" if is_defensive else "outgoing"

    dmg_stats = pilot_dmg if is_offensive else pilot_dmg_taken

    figures = []
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

        fig.subplots_adjust(bottom=0.23)

        ax_hp.set_facecolor("#0c0c1a")  # deep space navy
        fig.patch.set_facecolor("#0c0c1a")  # figure background
        colors = iter(plt.cm.tab10.colors)

        hp_max = 0

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
        # todo this errors. we dont have any match compsdata
        #  or users
        match_comp = sorted(
            match_comp,
            key=lambda s: (s.get("name").lower(), s["pilot"].lower())
        )

        fleet_dps_by_ts = defaultdict(float)
        fleet_reps_by_ts = defaultdict(float)
        for pilot in unique_pilots:
            color = next(colors)
            dps_by_ts = defaultdict(float)
            drone_dps_by_ts = defaultdict(float)
            pilot_reloads = []
            pilot_drone_engagements = []
            pilot_jammed = []

            # parse out damage,
            for e in damage_list:
                action_ts = datetime.strptime(e["action_timestamp"], '%Y-%m-%d %H:%M:%S')
                if (
                    cd_start <= action_ts <= end_dt
                    and is_involving_pilot(e, pilot)
                    and (e["direction"] == dmg_direction or e["direction"] == f"{dmg_direction}-breacher-pods")
                ):
                    dps_by_ts[action_ts] += e["rolling_dps"]
                    hp_max = max(hp_max, e["rolling_dps"], dps_by_ts[action_ts])

                if (
                    cd_start <= action_ts <= end_dt
                    and is_involving_pilot(e, pilot)
                    and e["direction"] in (f"{dmg_direction}-drones", f"{dmg_direction}-drones-drones")
                ):
                    drone_dps_by_ts[action_ts] += e["rolling_dps"]
                    hp_max = max(hp_max, e["rolling_dps"], drone_dps_by_ts[action_ts])

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
                    action_ts = datetime.strptime(e["action_timestamp"], '%Y-%m-%d %H:%M:%S')

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
                    ab = AnnotationBbox(img, (reload, reload_x), frameon=False, zorder=500)
                    ax_x2.add_artist(ab)

                reload_x -= 5

                # todo map out jams here
                #for jam in pilot_jammed:
                #    img = OffsetImage(ctx.jam_img, zoom=.5)
                #    ab = AnnotationBbox(img, (jam, jam_x), frameon=False, zorder=500)
                #    ax_x2.add_artist(ab)

                for drone in pilot_drone_engagements:
                    img = OffsetImage(ctx.drone_img, zoom=.5)
                    ab = AnnotationBbox(img, (drone, drone_engage_x), frameon=False, zorder=500)
                    ax_x2.add_artist(ab)

                drone_engage_x += 5

            # add in first actions for this pilot
            this_pilots_first_action = []
            for first_actions in match_first_actions:
                if first_actions['pilot'] == pilot:
                    this_pilots_first_action.append(first_actions.get('ts'))

            # sort and get values for dmg
            ts_sorted = sorted(dps_by_ts.keys())
            dps_values = [dps_by_ts[ts] for ts in ts_sorted]

            dps_ems = compute_ema(dps_values, alpha)

            drones_sorted = sorted(drone_dps_by_ts.keys())
            drone_values = [drone_dps_by_ts[ts] for ts in drones_sorted]

            drone_ems = compute_ema(drone_values, alpha)

            ts_sorted = [datetime.fromisoformat(str(t)) for t in ts_sorted]            # Guns / pods DPS — solid

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
                    hp_max = max(hp_max, e["rolling_reps"], fleet_reps_by_ts[action_ts])

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

        for e in fleet_dmg:
            action_ts = datetime.strptime(e["action_timestamp"], '%Y-%m-%d %H:%M:%S')

            if (
                cd_start <= action_ts <= end_dt
                and (e["direction"] in [dmg_direction, f"{dmg_direction}-breacher-pods", f"{dmg_direction}-drones"])
            ):
                ts = e["action_timestamp"]
                fleet_dps_by_ts[ts] += e["rolling_dps"]
                hp_max = max(hp_max, e["rolling_dps"], fleet_dps_by_ts[ts])

        fleet_dps_sorted = sorted(fleet_dps_by_ts.keys())
        fleet_dps_values = [fleet_dps_by_ts[ts] for ts in fleet_dps_sorted]

        fleet_dps_sorted = [datetime.fromisoformat(f) for f in fleet_dps_sorted]

        ema = compute_ema(fleet_dps_values, alpha)

        death_plots = []
        for death in pilot_deaths:
            if death['seconds_before_match_end'] > 10 and death['match_id'] == this_match_id:
                death_plots.append(death['last_action_ts'])

        for death_ts in death_plots:
            img = OffsetImage(skull_img, zoom=.03)
            ab = AnnotationBbox(img, (death_ts, death_x), frameon=False, zorder=500, annotation_clip=True)
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

        ax_hp.set_ylim(0, (hp_max * 1.1))
        ax_x2.set_ylim(0, 100)

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
                    zorder=5
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
