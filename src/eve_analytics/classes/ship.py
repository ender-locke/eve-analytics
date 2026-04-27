

class Ship:
    """


    """
    def __init__(self, ship_name):
        self.name = ship_name
        self.id = self._get_ship_id(ship_name)

    def __repr__(self) -> str:
        """

        :return:
        """

        return f"<Ship> {self.name}"

    def _get_ship_id(self, ship) -> int:
        # todo connect to pyfa db and get it
        return 0
