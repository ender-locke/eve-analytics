import re
from datetime import datetime
import html


def _parse_attacker(raw):
    """
    Extract pilot, corp, ship from EVE-style strings.
    Examples handled:
      'jommy Virpio[3MPKT](Cynabal)'
      'Issac Igunen [3MPKT] Garmur'
      'Cynabal [3MPKT] [jommy Virpio]'
    """

    raw = raw.strip()

    # Extract corp in square brackets
    corp_match = re.search(r'\[([^\]]+)\]', raw)
    corp = corp_match.group(1) if corp_match else None

    # Extract ship in parentheses
    ship_match = re.search(r'\(([^)]+)\)', raw)
    ship = ship_match.group(1) if ship_match else None

    # Remove corp/ship chunks
    cleaned = re.sub(r'\[.*?\]|\(.*?\)', "", raw).strip()

    pilot = cleaned if cleaned else None

    return {
        "pilot": pilot,
        "corp": corp,
        "ship": ship,
    }


def _parse_entity(s):
    s = s.strip()

    # Special case
    if s.lower() == "you":
        return {"pilot": "you", "corp": None, "ship": None}

    # Extract bracketed values (corp, pilot)
    bracketed = re.findall(r'\[([^\]]+)\]', s)

    # Remove bracketed segments from the string to isolate words
    clean = re.sub(r'\[[^\]]+\]', '', s).strip()

    # Get remaining words
    parts = clean.split()

    # Case: pilot [corp] ship
    if len(bracketed) == 1 and len(parts) >= 2:
        pilot = " ".join(parts[:-1])
        ship = parts[-1]
        corp = bracketed[0]
        return {"pilot": pilot, "corp": corp, "ship": ship}

    # Case: ship [corp] [pilot]
    if len(bracketed) == 2 and len(parts) == 1:
        ship = parts[0]
        corp = bracketed[0]
        pilot = bracketed[1]
        return {"pilot": pilot, "corp": corp, "ship": ship}

    # Case: something else, fallback
    return {
        "pilot": " ".join(parts),
        "corp": bracketed[0] if bracketed else None,
        "ship": None if len(parts) == 1 else parts[-1],
    }


def _clean_lines(lines: str) -> str:
    text = lines
    text = re.sub(r'(?i)<br\s*/?>', '\n', text)
    text = re.sub(r'(?is)<a[^>]*>(.*?)</a>', r'\1', text)
    text = re.sub(r'(?is)</?[^>\n]+?>', '', text)
    text = html.unescape(text)
    text = '\n'.join(line.rstrip() for line in text.splitlines())
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text


def parse_combat_log(combat_path):
    """
    Parse an EVE Online combat log file into structured event data.

    This function reads a raw combat log file and extracts relevant combat events
    such as damage, repairs, capacitor activity, electronic warfare, and utility
    actions. It normalizes these events into categorized lists of dictionaries
    that can be used for analytics, visualization, or storage.

    The parser handles both incoming and outgoing interactions for the log owner
    ("character"), including edge cases such as drones, capacitor warfare, and
    malformed or partially structured log lines.

    Parameters
    ----------
    combat_path : pathlib.Path
        Path to the combat log file to be parsed.

    Returns
    -------
    dict
        A dictionary containing categorized combat data and metadata:

        - "events" : list[tuple]
            Raw timeline events (timestamp, type, value, actor, target).
        - "dmg" : list[dict]
            Damage events (incoming and outgoing).
        - "reps" : list[dict]
            Remote repair and boosting events.
        - "cap_reps" : list[dict]
            Capacitor transfer events (currently reserved).
        - "nos" : list[dict]
            Energy vampire (NOS) events.
        - "neut" : list[dict]
            Energy neutralizer events.
        - "scrams" : list[dict]
            Warp scrambler interactions.
        - "jams" : list[dict]
            ECM (jamming) events.
        - "drones" : list[dict]
            Drone engagement events.
        - "reloads" : list[dict]
            Module reload events.
        - "links" : list[dict]
            Fleet command burst (link) activations.
        - "cap_warning" : list[dict]
            Capacitor warning events (e.g., low/empty cap).
        - "pilots" : list[str]
            Unique pilots detected (includes the log owner).
        - "lowest_log_ts" : datetime
            Earliest timestamp found in the log.
        - "skipped" : list[dict]
            Lines that could not be parsed, including original and cleaned versions.

    Notes
    -----
    - The log owner ("character") is inferred from the file header. If not found,
      it defaults to "Unknown".
    - All timestamps are parsed into `datetime` objects.
    - HTML formatting and tags are stripped before parsing.
    - Some partially matched or unsupported lines are collected in "skipped"
      for debugging and parser improvement.
    - Direction fields typically use:
        - "incoming"  : events affecting the character
        - "outgoing"  : events caused by the character

    Raises
    ------
    IOError
        If the file cannot be read.
    ValueError
        If timestamps cannot be parsed due to unexpected format.
    """
    damage_list = []
    reps_list = []
    cap_list = []
    nos_list = []
    neut_list = []
    scram_list = []
    cap_warnings_list = []
    jams_list = []
    drone_engaged_list = []
    reloading_list = []
    links_list = []
    skipped_lines = []
    unique_pilots = []

    file_name = combat_path.name.split("/")[-1]
    lowest_log_ts = None

    lines = combat_path.read_text(encoding="utf-8").splitlines()

    character = None

    for line in lines[:20]:  # search more lines
        clean = _clean_lines(line)
        match = re.search(r'listener\s*:\s*(.+)$', clean, re.IGNORECASE)
        if match:
            character = match.group(1).strip()
            break

    if not character:
        character = "Unknown"

    if character not in unique_pilots:
        unique_pilots.append(character)

    events = []
    line_re = re.compile(r'\[ ([\d.:\s]+) \] .*?\)\s*(.+)', re.IGNORECASE)

    for line in lines:
        match = line_re.search(line)
        if not match:
            skipped_lines.append({
                "file": file_name,
                "cleaned": _clean_lines(line),
                "og": line
            })
            continue

        timestamp_str, message = match.groups()
        timestamp = datetime.strptime(timestamp_str.strip(), "%Y.%m.%d %H:%M:%S")
        if lowest_log_ts is None or timestamp < lowest_log_ts:
            lowest_log_ts = timestamp

        message_lower = message.lower()
        cleaned_line = _clean_lines(message)

        # Incoming damage: from attacker -> character (log owner)
        incoming_match = re.search(
            r'''
            ^(?P<amount>\d+)\s+from\s+
            (?P<pilot_string>.+?)\s+-\s+
            (?P<module>.+?)\s+-\s+
            (?P<quality>Hits|Grazes|Glances|Penetrates|Smashes|Wrecks|Glances\ Off)$
            ''',
            cleaned_line,
            re.IGNORECASE | re.VERBOSE
        )
        if incoming_match:
            damage = float(incoming_match.group('amount'))
            attacker = incoming_match.group('pilot_string')
            pilot = _parse_attacker(attacker)
            module = incoming_match.group('module')
            quality = incoming_match.group('quality')
            events.append((timestamp, 'incoming', damage, character, pilot.get('pilot', 'unknown')))
            damage_list.append({
                "time": timestamp,
                "direction": 'incoming',
                "amount": damage,
                "to": character,
                "from": pilot.get('pilot', 'unknown'),
                "row_type": "damage",
                "hit_quality": quality,
                "module": module,
                "pilot": character,
                "og_line": line,
                "cleaned_line": cleaned_line
            })
            continue

        # Outgoing damage: character (log owner) -> target via weapon

        dmg_match = re.search(
            r"""
            (?P<damage>\d+(?:\.\d+)?)      # Damage amount (integer or decimal)
            \s+to\s+
            (?P<target>[^\[\(]+)           # Pilot name
            (?:\[(?P<corp>[^\]]+)\])?      # Optional corp tag
            (?:\((?P<ship>[^\)]+)\))?      # Optional ship
            \s*-\s*
            (?P<weapon>[^-]+?)             # Weapon name
            \s*-\s*
            (?P<quality>Hits|Grazes|Penetrates|Smashes|Wrecks|Glances\ Off|Misses)  # Hit quality
            """,
            cleaned_line,
            re.VERBOSE
        )
        if dmg_match:
            damage = float(dmg_match.group('damage'))
            target = dmg_match.group('target').strip()
            corp = dmg_match.group('corp')
            ship = dmg_match.group('ship')
            weapon = dmg_match.group('weapon').strip()
            quality = dmg_match.group('quality')

            events.append((timestamp, 'dps', damage, character, weapon))
            damage_list.append({
                "time": timestamp,
                "direction": 'outgoing',
                "amount": damage,
                "from": character,
                "to": target,
                "module": weapon,
                "hit_quality": quality,
                "row_type": "damage",
                "pilot": character,
                "og_line": line,
                "cleaned_line": cleaned_line
            })
            continue

        # Zero damage event (missed)
        if "misses" in message_lower:
            events.append((timestamp, 'dps', 0, character))
            """damage_list.append({
                "time": timestamp,
                "direction": 'outgoing',
                "amount": damage,
                "from": character,
                "to": attacker,
                "module": weapon,
                "hit_quality": hit,
                "row_type": "damage"

            })"""
            continue

        # Remote repairs TO character (log owner)
        rep_match = re.search(
            r'<b>([\d.]+)</b>.*?remote (armor|shield|hull|capacitor) (repaired|boosted) by(.*?)-\s*([^<]+)',
            message,
            re.IGNORECASE
        )
        if rep_match:
            amount, rep_type, action, by_chunk, module = rep_match.groups()

            # Extract pilot (either [Name] or <i>Name</i>)
            pilot_match = re.search(r'\[([^\]]+)\]|<i>(.*?)</i>', by_chunk)
            logi_pilot = next((g for g in pilot_match.groups() if g), None) if pilot_match else None

            # Extract ship (usually bold)
            ship_match = re.search(r'<b>([^<]+)</b>', by_chunk)
            ship = ship_match.group(1) if ship_match else None
            events.append((timestamp, 'repairs', amount, character))
            reps_list.append({
                "time": timestamp,
                "direction": 'incoming',
                "rep_type": rep_type,
                "amount": amount,
                "to": character,
                "from": logi_pilot,
                "row_type": "reps",
                "module": module,
                "pilot": character,
                "og_line": line,
                "cleaned_line": cleaned_line
            })
            continue

        # Remote boosted to (armor|shield|hull) BY character to someone else
        boosted_match = re.search(
            r'([\d.]+)\s+remote\s+(armor|shield|hull|capacitor)\s+'
            r'(repaired|boosted)\s+to\s+(.+?)\s+-\s+(.+)',
            cleaned_line,
            re.IGNORECASE
        )
        if boosted_match:
            amount = float(boosted_match.group(1))
            rep_type = boosted_match.group(2).lower().strip()
            action = boosted_match.group(3)
            healed_pilot = "".join(boosted_match.group(4).strip().split(" ")[:-1])
            module = boosted_match.group(5).strip()
            events.append((timestamp, 'remote_reps', amount, character))
            if rep_type != "capacitor":
                reps_list.append({
                    "time": timestamp,
                    "direction": 'outgoing',
                    "rep_type": rep_type,
                    "amount": amount,
                    "from": character,
                    "to": healed_pilot,
                    "row_type": "reps",
                    "module": module,
                    "pilot": character,
                    "og_line": line,
                    "cleaned_line": cleaned_line
                })
            else:
                reps_list.append({
                    "time": timestamp,
                    "direction": 'outgoing',
                    "rep_type": rep_type,
                    "amount": amount,
                    "from": character,
                    "to": healed_pilot,
                    "row_type": "cap reps",
                    "module": module,
                    "pilot": character,
                    "og_line": line,
                    "cleaned_line": cleaned_line
                })
            continue

        nos_match = re.search(
            r"""
            (?P<amount>[+-]?\d+(?:\.\d+)?)\s*GJ\s+
            energy\s+drained\s+
            (?P<direction>from|to)\s+
        
            (?P<raw_target>.+?)\s*-\s*            # everything before dash
        
            (?P<module>.+)$
            """,
            cleaned_line,
            re.VERBOSE | re.IGNORECASE
        )
        if nos_match:
            amount = float(nos_match.group("amount"))
            direction = nos_match.group("direction")
            raw = nos_match.group("raw_target").strip()
            module = nos_match.group("module").strip()

            nos_character = None
            corp = None
            pilot = None
            ship = None

            # Case 1: Character [CORP] [Pilot]
            corp_pilot_match = (
                corp_pilot_match_a
                if (corp_pilot_match_a := re.match(
                    r"""
                    (?P<pilot>.+?)\s+
                    \[(?P<corp>[^\]]+)\]\s+
                    (?P<ship>[A-Za-z0-9'._\- ]+)
                    """,
                    raw,
                    re.VERBOSE
                )) else (
                    corp_pilot_match_b
                    if (corp_pilot_match_b := re.match(
                        r"""
                        (?P<ship>[A-Za-z0-9'._\- ]+)\s+
                        \[(?P<corp>[^\]]+)\]\s+
                        \[(?P<pilot>[^\]]+)\]
                        """,
                        raw,
                        re.VERBOSE
                    )) else None
                )
            )

            # Case 2: Pilot Ship
            pilot_ship_match = re.match(
                r"""
                (?P<pilot>.+?)\s+          # everything up to last space
                (?P<ship>[A-Za-z0-9'._\-]+)$
                """,
                raw,
                re.VERBOSE
            )

            if corp_pilot_match:
                #nos_character = corp_pilot_match.group("character").strip()
                corp = corp_pilot_match.group("corp").strip()
                pilot = corp_pilot_match.group("pilot").strip()

            elif pilot_ship_match:
                pilot = pilot_ship_match.group("pilot").strip()
                ship = pilot_ship_match.group("ship").strip()

            nos_list.append({
                "time": timestamp,
                "direction": "outgoing" if direction == "to" else "incoming",
                "amount": amount,
                "from": character if direction == "to" else pilot,
                "to": pilot if direction == "to" else character,
                "row_type": "nos",
                "module": module,
                "pilot": character,
                "og_line": line,
                "cleaned_line": cleaned_line
            })
            continue

        neutralizer_match = re.search(
            r'<b>([+-]?\d+(?:\.\d+)?)\s*GJ</b>.*?energy neutralized'
            r'.*?<b>([^<]+)</b>'        # Pilot
            r'(?:\s*\[([^\]]+)\])?'     # Optional corp ticker
            r'.*?<b>([^<]+)</b>?'       # Target ship (may be missing)
            r'.*?-\s*([^<]+)</font>',   # Module
            message,
            re.IGNORECASE | re.DOTALL
        )
        if neutralizer_match:
            amount = float(neutralizer_match.group(1))
            pilot = neutralizer_match.group(2).strip()
            corp = neutralizer_match.group(3)        # may be None
            target_ship = neutralizer_match.group(4) # may be None
            module = neutralizer_match.group(5).strip()
            direction = "outgoing" if pilot == character else "incoming" # to means youre neuting them, from means they are neuting you
            neut_list.append({
                "time": timestamp,
                "direction": direction,
                "amount": amount,
                "from": pilot if pilot == character else character,
                "to": character if pilot == character else pilot,
                "row_type": "neuts",
                "module": module,
                "pilot": character,
                "og_line": line,
                "cleaned_line": cleaned_line
            })
            continue

        if "warp scram" in cleaned_line.lower():
            if "you" in cleaned_line.lower():
                #print(cleaned_line)
                to_you_scram_match = re.search(r"""
                    warp\s+scram(?:ble|bler)?\s+attempt\s+from\s+
                    
                    (?P<from_string>(?:(?!\byou\b).)+?)      # from_string cannot contain "you"
                    
                    \s*(?:-\s*)?to\s+                        # optional dash before "to"
                    
                    (?P<to_string>.*?\byou\b.*?)             # to_string MUST contain "you"
                    
                    [!\-]*$                                   # optional tail punctuation
                """, cleaned_line, re.IGNORECASE | re.VERBOSE)

                from_you_scram_match = re.search(r"""
                    warp\s+scram(?:ble|bler)?\s+attempt\s+from\s+
                    
                    (?P<from_string>.*?\byou\b.*?)          # MUST contain 'you'
                    
                    \s*(?:-\s*)?to\s+                       # dash optional
                    
                    (?P<to_string>(?:(?!\byou\b).)+?)       # MUST NOT contain 'you'
                    
                    [!\-]*$                                 # optional trailing punctuation
                """, cleaned_line, re.IGNORECASE | re.VERBOSE)

                scram_match = to_you_scram_match if to_you_scram_match else from_you_scram_match
                #print(to_you_scram_match, from_you_scram_match, scram_match)

                if scram_match:
                    from_string = scram_match.group("from_string")
                    to_string = scram_match.group("to_string")

                    from_dict = _parse_entity(from_string)
                    to_dict = _parse_entity(to_string)

                    if from_string.lower() == "you":
                        from_pilot = character
                    else:
                        from_pilot = from_dict.get("pilot")

                    if to_string.lower() == "you":
                        to_pilot = character
                    else:
                        to_pilot = to_dict.get("pilot")

                    # Determine direction
                    if from_pilot == character:
                        direction = "outgoing"
                    elif to_pilot == character:
                        direction = "incoming"
                    else:
                        direction = None  # not involving this character
                    if direction:
                        scram_list.append({
                            "time": timestamp,
                            "from": from_pilot,
                            "to": to_pilot,
                            "row_type": "scrams",
                            "direction": direction,
                            "pilot": character,
                            "og_line": line,
                            "cleaned_line": cleaned_line
                        })
                    continue
        jam_simple_match = re.search(r"""
            ^\s*
            (?P<who>.+?)              # pilot + ship blob
            \s+jammed\s*-\s*
            (?P<module>.+)
            \s*$
        """, cleaned_line, re.IGNORECASE | re.VERBOSE)

        jam_match = re.search(r"""
            ^\s*
            (?P<ship>[A-Za-z0-9'._\- ]+)       # Ship name
            \s+\[(?P<corp>[^\]]+)\]            # [CorpTag]
            \s+\[(?P<pilot>[^\]]+)\]           # [PilotName]
            \s*-\s*jammed\s*-\s*
            (?P<module>.+?)                    # Jam module name
            \s*$                               # end of line
        """, cleaned_line, re.IGNORECASE | re.VERBOSE)

        being_jammed_match = re.search(
            r"You're jammed by\s+(?P<pilot>.*?)\s+(?P<ship>[A-Za-z0-9' -]+)\s+-\s+(?P<module>.+)",
            cleaned_line,
            re.IGNORECASE
        )

        if jam_match:
            pilot = jam_match.group("pilot")
            jams_list.append({
                "time": timestamp,
                "from": character,
                "to": pilot,
                "row_type": "jams",
                "direction": "outgoing",
                "pilot": character,
                "og_line": line,
                "cleaned_line": cleaned_line
            })
            continue

        if jam_simple_match:
            who = jam_simple_match.group("who")
            module = jam_simple_match.group("module")
            parts = who.split()
            ship = parts[-1]
            pilot = " ".join(parts[:-1])

            jams_list.append({
                "time": timestamp,
                "from": character,
                "to": pilot,
                "row_type": "jams",
                "direction": "outgoing",
                "pilot": character,
                "og_line": line,
                "cleaned_line": cleaned_line
            })
            continue

        if being_jammed_match:
            pilot = being_jammed_match.group("pilot")
            jams_list.append({
                "time": timestamp,
                "from": pilot,
                "to": character,
                "row_type": "jams",
                "direction": "incoming",
                "pilot": character,
                "og_line": line,
                "cleaned_line": cleaned_line
            })
            continue

        drone_match = re.search(r"^Drones engaging\s+(?P<target>.+)$", cleaned_line)
        if drone_match:
            drone_engaged_list.append({
                "time": timestamp,
                "from": character,
                "row_type": "drones",
                "direction": "outgoing",
                "pilot": character,
                "og_line": line,
                "cleaned_line": cleaned_line
            })
            continue

        links_match = re.search(r"""
            ^Your\s+                             # 'Your ' at start
            (?P<module>.+?)\s+                   # module name
            has\ applied\ bonuses\ to\s+         # literal text
            (?P<count>\d+)\s+                    # number of members
            fleet\ member[s]?\.                  # 'fleet member.' or 'fleet members.'
            $                                    # end of line
        """, cleaned_line, re.VERBOSE)
        if links_match:
            links_list.append({
                "time": timestamp,
                "from": character,
                "row_type": "links",
                "direction": "outgoing",
                "pilot": character,
                "og_line": line,
                "cleaned_line": cleaned_line
            })
            continue

        reload_match = re.search(r"""
            ^Loading\s+                                   # 'Loading' at start of line
            (?P<charge>.+?)\s+                              # item being loaded
            into\s+the\s+                                 # 'into the'
            (?P<module>.+?)                               # target module
            ;\s+this\ will\ take\ approximately\s+       # literal text
            (?P<reload_time>\d+)\s+seconds\.                     # number of seconds
            $                                             # end of line
        """, cleaned_line, re.IGNORECASE | re.VERBOSE)
        if reload_match:
            charge = reload_match.group("charge")
            module = reload_match.group("module")
            reload_time = reload_match.group("reload_time")
            reloading_list.append({
                "time": timestamp,
                "from": character,
                "module": f"{charge}|{module}",
                "row_type": "reloads",
                "direction": "outgoing",
                "pilot": character,
                "amount": reload_time,
                "og_line": line,
                "cleaned_line": cleaned_line
            })
            continue


        # Restore messages (common for NPC logs)
        if "restores" in message_lower:
            restore_match = re.search(r'restores ([\d.]+) hp', message, re.IGNORECASE)
            if restore_match:
                reps = float(restore_match.group(1))
                events.append((timestamp, 'repairs', reps, character))
                continue
                # Capacitor warnings
        elif (
                "capacitor is empty" in message_lower
                or "neutralized" in message_lower
                or re.search(r'requires [\d.]+ units of charge\. the capacitor has only [\d.]+ units\.', message_lower)
        ):
            events.append((timestamp, 'cap_warn', 1, character))
            if "neutralized" not in message_lower:
                # todo ender add cap warnings here
                cap_warnings_list.append({
                    "time": timestamp,
                    "to": character,
                    "from": character,
                    "direction": "incoming",
                    "row_type": "cap warning",
                    "pilot": character,
                    "og_line": line,
                    "cleaned_line": cleaned_line
                })
            continue

        skipped_lines.append({
            "file": file_name,
            "cleaned": _clean_lines(message),
            "og": message
        })

    return {
        "events": events,
        "neut": neut_list,
        "dmg": damage_list,
        "reps": reps_list,
        "cap_reps": cap_list,
        "nos": nos_list,
        "scrams": scram_list,
        "skipped": skipped_lines,
        "jams": jams_list,
        "drones": drone_engaged_list,
        "reloads": reloading_list,
        "links": links_list,
        "cap_warning": cap_warnings_list,
        "pilots": unique_pilots,
        "lowest_log_ts": lowest_log_ts
    }
