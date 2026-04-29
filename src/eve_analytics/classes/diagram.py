from eve_analytics.diagrams.queries.eve import (get_drones, get_damage_output_stats,
                                                get_first_actions, get_log_data,
                                                get_matches, get_unique_pilots)

class MatchAnalytics:

    def __int__(self, ea, match_id, ):
        self._ea = ea
        self.match_id = match_id
        self.__build_match_datasets()
        pass

    def __build_match_datasets(self):
        db = self._ea.db

        pass
