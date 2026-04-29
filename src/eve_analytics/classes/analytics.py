from eve_analytics.diagrams.queries.eve import (get_drones, get_damage_output_stats,
                                                get_first_actions, get_log_data, get_pilots_and_ships,
                                                get_matches, get_unique_pilots, get_match_last_action_by_pilot,
                                                get_fleet_rolling_reps, get_fleet_rolling_dps, get_rolling_dps_bp,
                                                get_rolling_dps_w_pilots)
from collections import defaultdict


class MatchAnalytics:

    def __int__(self, ea, match_id, fc):
        self._ea = ea
        self._fc = fc
        self._match_id = match_id
        self.__build_match_datasets()
        self.__build_out_damage()
        self.__build_pilot_n_ships()
        pass

    @property
    def match_id(self):
        return self._match_id

    def __build_match_datasets(self):
        db = self._ea.db
        self.all_dmg = get_rolling_dps_bp(seconds=self._fc.query_vars['dps_secs'], match_id=self._match_id, db=db)
        self.all_neuts = get_log_data(db, "neuts", self._match_id)
        self.all_reps = get_log_data(db,"reps", self._match_id)
        self.all_nos = get_log_data(db,"nos", self._match_id)
        self.all_scrams = get_log_data(db,"scrams", self._match_id)
        self.all_jams = get_log_data(db,"jams", self._match_id)
        self.all_drones = get_log_data(db,"drones", self._match_id)
        self.all_links = get_log_data(db,"links", self._match_id)
        self.all_reloads = get_log_data(db,'reloads', self._match_id)
        self.all_cap_warnings = get_log_data(db,"cap warning", self._match_id)
        self.first_actions = get_first_actions(db, self._match_id)
        self.unique_pilots = get_unique_pilots(db, self._match_id)
        self.dmg_output_stats = get_damage_output_stats(db, self._match_id)
        self.dmg_input_stats = get_damage_output_stats(db, self._match_id, direction="incoming")
        self.fleet_dps = get_fleet_rolling_dps(db, seconds=self._fc.query_vars['dps_secs'], match_id=self._match_id)
        self.ships_and_pilots = get_pilots_and_ships(db, self._match_id)
        self.fleet_reps = get_fleet_rolling_reps(db, seconds=self._fc.query_vars['dps_secs'], match_id=self._match_id)
        self.pilot_deaths = get_match_last_action_by_pilot(db=db, match_id=self._match_id)


        pass


    def __build_pilot_n_ships(self):
        pilots_w_ships = defaultdict(list)

        for pilot_row in self.ships_and_pilots:
            pilots_w_ships[pilot_row['pilot']].append(pilot_row)

    def __build_out_damage(self):
        new_all_dmg = []

        for dmg in self.all_dmg:
            dmg_dict = dict(dmg)
            if self._fc.drone_dps:
                if dmg_dict.get("is_drone"):
                    dmg_dict["direction"] = f"{dmg_dict['direction']}-drones"
            if self._fc.pod_dps:
                if dmg_dict.get("is_breacher_pod"):
                    dmg_dict["direction"] = f"{dmg_dict['direction']}-breacher-pods"

            new_all_dmg.append(dmg_dict)

        self.all_dmg = new_all_dmg


    def __build_fleet_digrams(self):
        pass

    def __build_pilot_diagrams(self):
        pass