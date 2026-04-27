#from eve_analytics.classes import Ship


class Pilot:
    """


    """
    def __repr__(self) -> str:
        """

        :return:
        """

        return f"<Pilot> {self.name}"

    def __init__(self, pilot_name, match, ship_data):
        self.name = pilot_name
        self.match = match
        #self.ship = Ship()


