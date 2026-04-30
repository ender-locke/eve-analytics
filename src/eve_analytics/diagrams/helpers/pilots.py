

def is_involving_pilot(event, pilot_name):
    event = dict(event)
    return (event.get("from") == pilot_name or event.get("to") == pilot_name
            or event.get("action_from") == pilot_name or event.get("action_to") == pilot_name
            or event.get("pilot") == pilot_name)
