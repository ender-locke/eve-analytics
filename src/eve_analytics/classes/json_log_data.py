

class JSONLogData:

    def __int__(self, name, data):
        self.name = name
        self.data = data

    def __repr__(self) -> str:
        """

        :return:
        """

        return f"<JSONLogData> | {self.name}"

