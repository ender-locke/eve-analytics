from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import matplotlib.pyplot as plt
from datetime import timedelta
import urllib.request
from PIL import Image
import numpy as np
from collections import defaultdict
from .helpers.icons import get_eve_icon

illegal_color = (0.3, 0, 0, 0.3)   # dark red with 30% opacity
alpha = 0.15

def generate_pilot_flight_diagrams(
        pilot_name,
        matches,
        damage_list,
        reps_list,
        nos_list,
        neut_list,
        cap_warnings_list,
        scram_list,
        jam_list,
        drone_list,
        links_list,
        reload_list,
        ctx,
        pilots_ships
):
    """
    Returns a list of matplotlib figures, one per match, for a single pilot.
    """

    with urllib.request.urlopen(ctx.icons["cap"]) as response:
        cap_img = np.array(Image.open(response))

    with urllib.request.urlopen(ctx.icons["links"]) as response:
        links_img = np.array(Image.open(response))

    with urllib.request.urlopen(ctx.icons["reload"]) as response:
        reload_img = np.array(Image.open(response))

    with urllib.request.urlopen(ctx.icons["being_scrammed"]) as response:
        being_scrammed_img = np.array(Image.open(response))

    with urllib.request.urlopen(ctx.icons["ecm"]) as response:
        ecm_img = np.array(Image.open(response))

    with urllib.request.urlopen(ctx.icons["drone"]) as response:
        drone_img = np.array(Image.open(response))

    with urllib.request.urlopen(ctx.icons["scram"]) as response:
        scram_img = np.array(Image.open(response))

    hp_max = 0
    figures = []

    def is_involving_pilot(event):
        return (event.get("from") == pilot_name or event.get("to") == pilot_name
                    or event.get("action_from") == pilot_name or event.get("action_to") == pilot_name
                    or event.get("pilot") == pilot_name)

    in_dmg = defaultdict(list)
    out_dmg = defaultdict(list)
    in_dmg_drones = defaultdict(list)
    out_dmg_drones = defaultdict(list)
    in_dmg_pods = defaultdict(list)
    out_dmg_pods = defaultdict(list)

    for match in matches:
        start = match["start"]
        cd_start = (start - timedelta(seconds=15))
        end = match["end"]
        match_minutes = int((end - start).total_seconds() // 60) + 1
        label = match.get("description", f"Match {match['id']}")
        this_ship = None

        for ship in pilots_ships:
            if ship['match_id'] == match['id']:
                this_ship = {
                    "name": ship['typeName'],
                    "id": ship["ship_id"]
                }

        for e in damage_list:
            if cd_start <= e["action_timestamp"] <= end and is_involving_pilot(e):
                if e['direction'] == "outgoing-drones-drones":
                    e['direction'] = "outgoing-drones"
                if e['direction'] == "incoming-drones-drones":
                    e['direction'] = "incoming-drones"

                key = (e["pilot"], e["direction"])
                if e['direction'] == "incoming":
                    in_dmg[key].append(e)
                elif e['direction'] == "outgoing":
                    out_dmg[key].append(e)
                elif e['direction'] == "outgoing-drones":
                    out_dmg_drones[key].append(e)
                elif e['direction'] == "incoming-drones":
                    in_dmg_drones[key].append(e)
                elif e['direction'] == "outgoing-breacher-pods":
                    out_dmg_pods[key].append(e)
                elif e['direction'] == "incoming-breacher-pods":
                    in_dmg_pods[key].append(e)
                if e['rolling_dps'] > hp_max:
                    hp_max = e['rolling_dps']

        reps = [e for e in reps_list if cd_start <= e["action_timestamp"] <= end and is_involving_pilot(e)]
        nos = [e for e in nos_list if cd_start <= e["action_timestamp"] <= end and is_involving_pilot(e)]
        neuts = [e for e in neut_list if cd_start <= e["action_timestamp"] <= end and is_involving_pilot(e)]
        scrams = [e for e in scram_list if cd_start <= e["action_timestamp"] <= end and is_involving_pilot(e)]
        jams = [e for e in jam_list if cd_start <= e["action_timestamp"] <= end and is_involving_pilot(e)]
        drones = [e for e in drone_list if cd_start <= e["action_timestamp"] <= end and is_involving_pilot(e)]
        reloads = [e for e in reload_list if cd_start <= e["action_timestamp"] <= end and is_involving_pilot(e)]
        links = [e for e in links_list if cd_start <= e["action_timestamp"] <= end and is_involving_pilot(e)]
        cap_warnings = [e for e in cap_warnings_list if cd_start <= e["action_timestamp"] <= end and is_involving_pilot(e)]

        if all(len(lst) == 0 for lst in [in_dmg, in_dmg_drones, out_dmg, out_dmg_drones,
                                         reps, nos, neuts, scrams, cap_warnings]):
            continue

        reps_in = [e for e in reps if e['direction'] == "incoming"]
        reps_out = [e for e in reps if e['direction'] == "outgoing"]

        nos_in = [e for e in nos if e['direction'] == "incoming"]
        nos_out = [e for e in nos if e['direction'] == "outgoing"]

        neuts_in = [e for e in neuts if e['direction'] == "incoming"]
        neuts_out = [e for e in neuts if e['direction'] == "outgoing"]

        fig, ax_hp = plt.subplots(figsize=(14, 6))
        ax_gj = ax_hp.twinx()

        ax_hp.set_facecolor("#0c0c1a")  # deep space navy
        fig.patch.set_facecolor("#0c0c1a")  # figure background

        if this_ship:
            ship_img = get_eve_icon(ctx.icons["base"], str(this_ship['id']))
            ship_box = OffsetImage(ship_img, zoom=1.20)
            ship_box.set_alpha(0.12)

            ship_ab = AnnotationBbox(
                ship_box,
                (0.175, 0.50),
                xycoords=fig.transFigure,
                frameon=False,
                box_alignment=(0.5, 0.5),
                zorder=0
            )

            ax_hp.add_artist(ship_ab)


        damage_series = {
            "incoming": in_dmg,
            "outgoing": out_dmg,
            "incoming drone": in_dmg_drones,
            "outgoing drone": out_dmg_drones,
            "incoming pods": in_dmg_pods,
            "outgoing pods": out_dmg_pods
        }

        for dmg_key, cfg in ctx.damage.items():
            dmg_dict = damage_series.get(dmg_key)
            if not dmg_dict:
                continue

            color = cfg["hex"]

            if ctx.dps_summed:
                dps_by_ts = defaultdict(float)

                all_directions = []
                for (pilot, direction), points in dmg_dict.items():
                    for p in points:
                        ts = p["action_timestamp"]
                        dps_by_ts[(ts, direction)] += p["rolling_dps"]
                        if direction not in all_directions:
                            all_directions.append(direction)

                for direction in all_directions:
                    ts_sorted = sorted(ts for ts, d in dps_by_ts if d == direction)
                    dps_values = [dps_by_ts[ts, direction] for ts in ts_sorted]

                    ema = []
                    for i, value in enumerate(dps_values):
                        if i == 0:
                            ema.append(value)
                        else:
                            ema.append(alpha * value + (1 - alpha) * ema[i-1])

                    ax_hp.plot(
                        ts_sorted,
                        ema,
                        label=f"{direction.capitalize()}",
                        color=color,
                        linewidth=2.5,
                        alpha=0.95
                    )

            else:
                for (frm, to, direction), points in dmg_dict.items():
                    points.sort(key=lambda e: e["action_timestamp"])

                    ax_hp.plot(
                        [p["action_timestamp"] for p in points],
                        [p["rolling_dps"] for p in points],
                        color=color,
                        label=f"{dmg_key}: {frm} → {to}",
                        alpha=0.85
                    )

        reps_in.sort(key=lambda e: e["action_timestamp"])
        ax_hp.plot(
            [ri['action_timestamp'] for ri in reps_in],
            [ri['amount'] for ri in reps_in],
            color=ctx.colors['incoming_reps_hex'],
            label="Reps In"
        )

        reps_out.sort(key=lambda e: e["action_timestamp"])
        ax_hp.plot(
            [ro['action_timestamp'] for ro in reps_out],
            [ro['amount'] for ro in reps_out],
            color=ctx.colors['outgoing_reps_hex'],
            label="Reps Out"
        )

        neuts_in.sort(key=lambda e: e["action_timestamp"])
        neuts_out.sort(key=lambda e: e["action_timestamp"])
        nos_out.sort(key=lambda e: e["action_timestamp"])
        nos_in.sort(key=lambda e: e["action_timestamp"])

        if ctx.gj_scatter:

            ax_gj.scatter(
                [ni['action_timestamp'] for ni in neuts_in],
                [abs(ni['amount']) for ni in neuts_in],
                marker="o",
                s=100,
                color=ctx.colors['incoming_neuts_hex'],
                label="Neuts In"
            )

            ax_gj.scatter(
                [no['action_timestamp'] for no in neuts_out],
                [abs(no['amount']) for no in neuts_out],
                marker="+",
                s=100,
                color=ctx.colors['outgoing_neuts_hex'],
                label="Neuts Out"
            )

            ax_gj.scatter(
                [no['action_timestamp'] for no in nos_out],
                [abs(no['amount']) for no in nos_out],
                marker='*',
                s=100,                     # size (area, not radius)
                color=ctx.colors['outgoing_nos_hex'],
                label="Nos Out"
            )

            ax_gj.scatter(
                [ni['action_timestamp'] for ni in nos_in],
                [abs(ni['amount']) for ni in nos_in],
                marker="x",
                s=100,
                color=ctx.colors['incoming_nos_hex'],
                label="Nos In"
            )

        else:
            ax_gj.plot(
                [ni['action_timestamp'] for ni in neuts_in],
                [abs(ni['amount']) for ni in neuts_in],
                color=ctx.colors['incoming_neuts_hex'],
                label="Neuts In"
            )

            ax_gj.plot(
                [no['action_timestamp'] for no in neuts_out],
                [abs(no['amount']) for no in neuts_out],
                color=ctx.colors['outgoing_neuts_hex'],
                label="Neuts Out"
            )

            ax_gj.plot(
                [no['action_timestamp'] for no in nos_out],
                [abs(no['amount']) for no in nos_out],
                color=ctx.colors['outgoing_nos_hex'],
                label="Nos Out"
            )

            nos_in.sort(key=lambda e: e["action_timestamp"])
            ax_gj.plot(
                [ni['action_timestamp'] for ni in nos_in],
                [abs(ni['amount']) for ni in nos_in],
                color=ctx.colors['incoming_nos_hex'],
                label="Nos In"
            )
        all_gj_events = nos_in + nos_out + neuts_out + neuts_in

        amounts = [abs(e["amount"]) for e in all_gj_events if e.get("amount") is not None]

        if amounts:
            max_gj = max(amounts)
            min_gj = 0
        else:
            max_gj = 10
            min_gj = 0

        cap_warning_marker = (max_gj + min_gj) / 2

        for scram in scrams:
            if scram['direction'] == "incoming":
                time = scram["action_timestamp"]
                img = OffsetImage(being_scrammed_img, zoom=0.5)  # zoom controls size
                ab = AnnotationBbox(img, (time, 20), frameon=False, xycoords='data')
                ax_hp.add_artist(ab)

            elif scram['direction'] == "outgoing":
                time = scram["action_timestamp"]  # x-axis coordinate
                img = OffsetImage(scram_img, zoom=0.5)  # zoom controls size
                ab = AnnotationBbox(img, (time, 20), frameon=False, xycoords='data')
                ax_hp.add_artist(ab)

        for jam in jams:
            if jam['direction'] == "outgoing":
                img_box = OffsetImage(ecm_img, zoom=.5)  # adjust zoom as needed
                ab = AnnotationBbox(img_box, (jam["action_timestamp"], 30), frameon=False)
                ax_hp.add_artist(ab)

        for link in links:
            if link['direction'] == "outgoing":
                img = OffsetImage(links_img, zoom=.5)
                ab = AnnotationBbox(img, (link['action_timestamp'], 60), frameon=False)
                ax_hp.add_artist(ab)

        for reload in reloads:
            if reload['direction'] == "outgoing":
                img = OffsetImage(reload_img, zoom=.5)
                ab = AnnotationBbox(img, (reload['action_timestamp'], 60), frameon=False)
                ax_hp.add_artist(ab)

        for drone in drones:
            if drone['direction'] == "outgoing":
                img = OffsetImage(drone_img, zoom=.5)
                ab = AnnotationBbox(img, (drone["action_timestamp"], 50), frameon=False)
                ax_hp.add_artist(ab)

        # Cap Warnings
        for warning in cap_warnings:
            time = warning["action_timestamp"]
            img = OffsetImage(cap_img, zoom=.5)
            ab = AnnotationBbox(img, (time, cap_warning_marker))
            ax_gj.add_artist(ab)

        ax_hp.set_xlim(cd_start, end)
        ax_gj.set_xlim(cd_start, end)

        ax_hp.set_ylim(0, (hp_max * 1.1))
        ax_gj.set_ylim(0, (max_gj * 1.1))

        ax_hp.tick_params(colors="white")
        ax_gj.tick_params(colors="white")

        ax_hp.set_title(f"Flight Diagram: {pilot_name} — {this_ship['name'] if this_ship else '-'} — {label}", color="white", pad=20)

        ax_hp.legend(
            loc="upper left",
            facecolor="#1a1a2e",
            edgecolor="white",
            labelcolor="white"
        )

        ax_gj.legend(
            loc="upper right",
            facecolor="#1a1a2e",
            edgecolor="white",
            labelcolor="white"
        )

        ax_hp.set_xlabel("Time (Eve)", color="white")
        ax_hp.set_ylabel("HP (Damage/Reps)", color="white")
        ax_gj.set_ylabel("GJ (Energy)", color="white")

        ax_hp.grid(True, linestyle='--', alpha=0.3, color="white")

        ax_hp.axvspan(cd_start, start, facecolor=illegal_color, edgecolor=None)
        ax_gj.axvspan(cd_start, start, facecolor=illegal_color, edgecolor=None)

        for i in range(match_minutes):
            x = start + timedelta(minutes=i)

            ax_gj.axvline(
                x,
                color="white",
                linestyle=":",   # '--', ':', '-.', etc.
                alpha=0.25,
                linewidth=3
            )

            ax_gj.text(
                x,
                1.01,                # slightly above the plot
                str(i),
                transform=ax_gj.get_xaxis_transform(),
                ha="center",
                va="bottom",
                color="white",
                fontsize=8,
                alpha=0.85
            )

        figures.append({
            "fig": fig,
            "name": f"{pilot_name}_{label.replace(' ', '_')}",
            "pilot": pilot_name
        })

    return figures