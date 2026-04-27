# EveAnalytics

**EveAnalytics** is a Python package for parsing EVE Online combat logs and turning them into structured data and visual diagrams.

It helps you go from raw `.txt` logs → usable datasets → insights about fights, fleets, and pilot activity.

---

## Features

* Parse EVE combat log files into structured data
* Aggregate events like:

    * Damage (`dmg`)
    * Neutralizers / Nosferatu (`neut`, `nos`)
    * Repairs (`reps`, `cap_reps`)
    * Electronic warfare (`jams`, `scrams`)
    * Drones, reloads, links, and more
* Build datasets for analysis or visualization
* Designed to support diagram generation (fleet fights, timelines, etc.)

---

## Installation

```bash
pip install eveanalytics
```

*(or install locally if not published)*

```bash
git clone https://github.com/yourusername/eveanalytics.git
cd eveanalytics
pip install -e .
```

---

## Quick Start

```python
from eve_analytics import EveAnalytics

ea = EveAnalytics(log_directory="/path/to/logs")

results = ea.parse_logs()

print(results)
```

---

## Setting the Log Directory

You can initialize with a directory:

```python
ea = EveAnalytics(log_directory="/path/to/logs")
```

Or set it later:

```python
ea = EveAnalytics()
ea.set_log_directory("/path/to/logs")
```

---

## Supported Log Data

Each parsed log may include:

* `dmg` — damage events
* `reps` — repair events
* `neut` / `nos` — capacitor warfare
* `jams` — ECM events
* `scrams` — tackle events
* `drones` — drone activity
* `reloads` — weapon reloads
* `links` — command bursts
* `cap_warning` — capacitor warnings
* `skipped` — unparsed/ignored lines

---

## Example: Working with Parsed Data

```python
results = ea.parse_logs()

for log in results:
    print(log["dmg"])
```

---

## Error Handling

The package includes custom exceptions:

* `LogLocationError` — invalid directory path
* `LogDirectoryNotSetError` — parsing attempted without setting a directory

---

## Project Structure

```
eve_analytics/
├── ingest/
│   └── splicer.py
├── exceptions/
│   └── file_errors.py
├── __init__.py
```

---

## Roadmap

* [ ] Diagram generation (timeline / fleet engagement visuals)
* [ ] Aggregated fight summaries
* [ ] Pilot-level statistics
* [ ] Export to CSV / Pandas DataFrames
* [ ] Visualization integrations (matplotlib / web UI)

---

## Contributing

Contributions are welcome. Open an issue or submit a PR.

---

## License

MIT License

---

## Disclaimer

EveAnalytics is a third-party tool and is not affiliated with CCP Games or EVE Online.
