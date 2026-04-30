

def is_involving_pilot(event, pilot_name):
    """
    Determines whether a combat log event involves a specific pilot.

    The function checks multiple possible fields where a pilot may appear,
    including both raw and normalized keys.

    Args:
        event (dict | sqlite3.Row): Combat log event record.
        pilot_name (str): Pilot name to check for involvement.

    Returns:
        bool: True if the pilot is involved in the event, otherwise False.

    Notes:
        The function checks the following fields:
        - 'from'
        - 'to'
        - 'action_from'
        - 'action_to'
        - 'pilot'
    """
    event = dict(event)
    return (event.get("from") == pilot_name or event.get("to") == pilot_name
            or event.get("action_from") == pilot_name or event.get("action_to") == pilot_name
            or event.get("pilot") == pilot_name)
