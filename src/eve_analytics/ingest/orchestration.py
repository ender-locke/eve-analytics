import uuid
import pandas as pd
from eve_analytics.data import log_keys
from eve_analytics.ingest.matches import parse_match_intervals
from eve_analytics.ingest.splicer import parse_combat_log
from eve_analytics.exceptions import MissingFilesError
from eve_analytics.helpers.matches import get_match_id
from eve_analytics.output.local_out import save_to_local


def splice_my_logs(logs_location, save_dir = None, save_spliced_output_flag: bool = False):
    combat_files = []
    local_file = None
    for file in logs_location:
        if "local" in file.lower():
            if local_file:
                local_file += f"\n{file}"
            else:
                local_file = file
        else:
            combat_files.append(file)

        if not local_file and not combat_files:
            if local_file:
                missing = "combat logs"
            else:
                missing = "local logs"
            raise MissingFilesError(missing)

        match_intervals = parse_match_intervals(local_file)
        matches_list = []

        for idx, (start, end) in enumerate(match_intervals):
            match_num = idx + 1
            matches_list.append({
                "idx": match_num,
                "id": str(uuid.uuid4()),
                "start": start,
                "end": end,
                "description": f"match {match_num}"
            })

        all_neuts = []
        all_dmg = []
        all_reps = []
        all_nos = []
        all_scrams = []
        all_jams = []
        all_drones = []
        all_links = []
        all_reloads = []
        all_cap_warnings = []
        all_skipped = []
        unique_pilots = []
        for path in combat_files:
            combat_logs = parse_combat_log(path)
            events = combat_logs["events"]

            for key in log_keys:
                for entry in combat_logs[key]:
                    try:
                        entry["match_id"] = get_match_id(entry["time"], matches_list)
                    except KeyError as e:
                        print(e)

            all_nos.extend(combat_logs["nos"])
            all_neuts.extend(combat_logs['neut'])
            all_dmg.extend(combat_logs['dmg'])
            all_reps.extend(combat_logs['reps'])
            all_scrams.extend(combat_logs["scrams"])
            all_cap_warnings.extend(combat_logs["cap_warning"])
            all_skipped.extend(combat_logs['skipped'])
            all_jams.extend(combat_logs['jams'])
            all_drones.extend(combat_logs['drones'])
            all_reloads.extend(combat_logs['reloads'])
            all_links.extend(combat_logs['links'])
            for pilot in combat_logs['pilots']:
                if pilot not in unique_pilots:
                    unique_pilots.append(pilot)

        output_dfs = {
            "reps": pd.DataFrame(all_reps),
            "neut": pd.DataFrame(all_neuts),
            "dmg": pd.DataFrame(all_dmg),
            "nos": pd.DataFrame(all_nos),
            "matches": pd.DataFrame(matches_list),
            "cap_warnings": pd.DataFrame(all_cap_warnings),
            "scrams": pd.DataFrame(all_scrams),
            "jams": pd.DataFrame(all_jams),
            "drones": pd.DataFrame(all_drones),
            "links": pd.DataFrame(all_links),
            "reloads": pd.DataFrame(all_reloads),
            "skipped": pd.DataFrame(all_skipped)
        }

        if save_spliced_output_flag:
            save_to_local(dfs=output_dfs, date=export_date, base_path=save_dir)
