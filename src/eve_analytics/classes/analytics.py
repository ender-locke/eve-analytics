from eve_analytics.diagrams.queries.eve import (get_drones, get_damage_output_stats,
                                                get_first_actions, get_log_data, get_pilots_and_ships,
                                                get_matches, get_unique_pilots, get_match_last_action_by_pilot,
                                                get_fleet_rolling_reps, get_fleet_rolling_dps_pd, get_rolling_dps_bp_pd,
                                                get_rolling_dps_w_pilots)
from collections import defaultdict
import matplotlib.pyplot as plt
from eve_analytics.diagrams.fleet_diagrams import generate_fleet_diagrams
from eve_analytics.diagrams.flight_diagrams import generate_pilot_flight_diagrams
from eve_analytics.diagrams.queries.client import get_match_timestamps
from eve_analytics.classes.pilot import Pilot
from pathlib import Path

class MatchAnalytics:
    """
    Generates analytics and visualizations for a single match.

    This class is responsible for:
    - Fetching match-specific data from the database
    - Building structured datasets for analysis
    - Computing pilot and fleet-level statistics
    - Generating fleet-wide and per-pilot diagrams

    The workflow is executed automatically on initialization.

    Attributes:
        _ea: EveAnalytics instance (provides database access).
        _fc (FlightContext): Configuration and feature flags for analytics.
        _match_id (str): Unique identifier for the match.
        _match_details (dict): Metadata for the match (start, end, countdown).
        _fleet_diagrams (list): Generated fleet-level diagram objects.
        _pilot_diagrams (list): Generated pilot-level diagram objects.
    """
    def __init__(self, ea, match_id, fc):
        """
        Initializes MatchAnalytics and builds all datasets and diagrams.

        Workflow:
        - Loads match metadata
        - Queries database for all relevant match data
        - Transforms and enriches datasets
        - Generates fleet and pilot diagrams

        Args:
            ea: EveAnalytics instance.
            match_id (str): Unique match identifier.
            fc (FlightContext): Flight context configuration.
        """
        self._ea = ea
        self._fc = fc
        self._match_id = match_id
        self.__get_match_details()
        self._fleet_diagrams = []
        self._pilot_diagrams = []
        self.__build_match_datasets()
        self.__build_out_damage()
        self.__build_pilot_n_ships()
        self.__build_fleet_diagrams()
        self.__build_pilot_diagrams()

    @property
    def match_id(self):
        """
        Returns the match identifier.

        Returns:
            str: Match ID.
        """
        return self._match_id

    def save_analytics(self, path):
        """
        Saves all generated diagrams to disk.

        Fleet and pilot diagrams are saved as PNG files using their
        assigned names or fallback indexed filenames.

        Args:
            path (str | Path): Directory where images will be saved.
        """
        folder = Path(path)
        folder.mkdir(parents=True, exist_ok=True)

        for i, fig in enumerate(self._fleet_diagrams):
            this_fig = fig.get('fig')
            this_fig.savefig(folder / f"{fig.get("name", f"fleet_{i}")}.png", bbox_inches="tight")
            plt.close(this_fig)

        for i, fig in enumerate(self._pilot_diagrams):
            this_fig = fig.get('fig')
            fig.get('fig').savefig(folder /  f"{fig.get("name", f"pilot_{i}")}.png", bbox_inches="tight")
            plt.close(this_fig)

    def __get_match_details(self):
        """
        Retrieves match timestamps and metadata from the database.

        Populates:
            self._match_details with:
            - id
            - start time
            - end time
            - countdown start time
        """
        match_details = get_match_timestamps(self._ea.db, self._match_id)
        self._match_details = {
            "id": self._match_id,
            "start": match_details[0][0],
            "end": match_details[0][1],
            "cd_start": match_details[0][2]
        }

    def __build_match_datasets(self):
        """
        Queries and constructs all datasets required for analytics.

        Includes:
        - Combat logs (damage, reps, neuts, etc.)
        - Pilot statistics (damage output/input)
        - Fleet metrics (DPS, reps)
        - Pilot lifecycle events (first actions, deaths)
        - Ship and pilot mappings
        """
        db = self._ea.db
        self.all_dmg = get_rolling_dps_bp_pd(seconds=self._fc.query_vars['dps_secs'], match_id=self._match_id, db=db)
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
        self.fleet_dps = get_fleet_rolling_dps_pd(db, seconds=self._fc.query_vars['dps_secs'], match_id=self._match_id)
        self.ships_and_pilots = get_pilots_and_ships(db, self._match_id)
        self.fleet_reps = get_fleet_rolling_reps(db, seconds=self._fc.query_vars['dps_secs'], match_id=self._match_id)
        self.pilot_deaths = get_match_last_action_by_pilot(db=db, match_id=self._match_id)

    def __build_pilot_n_ships(self):
        """
        Groups ship data by pilot.

        Builds a mapping of:
            pilot -> list of ship records

        Stored in:
            self.pilots_w_ships
        """
        self.pilots_w_ships = defaultdict(list)

        for pilot_row in self.ships_and_pilots:
            self.pilots_w_ships[pilot_row['pilot']].append(pilot_row)

    def __build_out_damage(self):
        """
        Normalizes and augments outgoing damage data.

        Modifies damage direction labels based on context flags:
        - Appends '-drones' if drone damage is enabled
        - Appends '-breacher-pods' if pod damage is enabled

        Updates:
            self.all_dmg
        """
        df = self.all_dmg.copy()

        if self._fc.drone_dps:
            mask = df["is_drone"].fillna(False).astype(bool)
            df.loc[mask, "direction"] = df.loc[mask, "direction"] + "-drones"

        if self._fc.pod_dps:
            mask = df["is_breacher_pod"].fillna(False).astype(bool)
            df.loc[mask, "direction"] = df.loc[mask, "direction"] + "-breacher-pods"

        self.all_dmg = df

    def __build_fleet_diagrams(self):
        """
       Generates fleet-level diagrams based on configuration flags.

       Supports:
       - Defensive diagrams
       - Offensive diagrams

       Diagrams are generated using shared match datasets and stored in:
           self._fleet_diagrams
       """
        if self._fc.generate_defensive_pilot_diagrams:
            pilot_graphs = generate_fleet_diagrams(
                diagram_type="defensive",
                unique_pilots=self.unique_pilots,
                matches=[self._match_details],
                damage_df=self.all_dmg,
                drone_list=self.all_drones,
                reload_list=self.all_reloads,
                first_actions_list=self.first_actions,
                pilot_dmg=self.dmg_output_stats,
                pilot_dmg_taken=self.dmg_input_stats,
                fleet_dmg=self.fleet_dps,
                fleet_reps=self.fleet_reps,
                pilot_deaths=self.pilot_deaths,
                fleet_jams=self.all_jams,
                ctx=self._fc,
                pilots_ships=self.pilots_w_ships
            )
            self._fleet_diagrams.extend(pilot_graphs)
        if self._fc.generate_offensive_pilot_diagrams:
            pilot_graphs = generate_fleet_diagrams(
                diagram_type="offensive",
                unique_pilots=self.unique_pilots,
                matches=[self._match_details],
                damage_df=self.all_dmg,
                drone_list=self.all_drones,
                reload_list=self.all_reloads,
                first_actions_list=self.first_actions,
                pilot_dmg=self.dmg_output_stats,
                pilot_dmg_taken=self.dmg_input_stats,
                fleet_dmg=self.fleet_dps,
                fleet_reps=self.fleet_reps,
                pilot_deaths=self.pilot_deaths,
                fleet_jams=self.all_jams,
                ctx=self._fc,
                pilots_ships=self.pilots_w_ships
            )
            self._fleet_diagrams.extend(pilot_graphs)

    def __build_pilot_diagrams(self):
        """
        Generates per-pilot flight diagrams.

        For each pilot:
        - Filters relevant datasets
        - Generates individual pilot visualizations

        Results are stored in:
            self._pilot_diagrams
        """
        if self._fc.generate_pilot_diagrams:
            for pilot in self.unique_pilots:
                pilot_graphs = generate_pilot_flight_diagrams(
                    pilot_name=pilot,
                    matches=[self._match_details],
                    damage_df=self.all_dmg,
                    reps_list=self.all_reps,
                    nos_list=self.all_nos,
                    neut_list=self.all_neuts,
                    cap_warnings_list=self.all_cap_warnings,
                    scram_list=self.all_scrams,
                    jam_list=self.all_jams,
                    drone_list=self.all_drones,
                    links_list=self.all_links,
                    reload_list=self.all_reloads,
                    ctx=self._fc,
                    pilots_ships=self.pilots_w_ships[pilot]
                )
                self._pilot_diagrams.extend(pilot_graphs)
