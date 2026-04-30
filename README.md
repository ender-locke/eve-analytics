# eve-analytics

[![Docs](https://img.shields.io/badge/docs-EVE_Analytics-blue?style=flat)](https://ender-locke.github.io/eve-analytics/)
![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/ender-locke/eve-analytics/deploy.yml)

![PyPI - Downloads](https://img.shields.io/pypi/dm/eve-analytics)
![PyPI - Version](https://img.shields.io/pypi/v/eve-analytics)
![PyPI - Status](https://img.shields.io/pypi/status/eve-analytics)
![PyPI - License](https://img.shields.io/pypi/l/eve-analytics)

![GitHub language count](https://img.shields.io/github/languages/count/ender-locke/eve-analytics)
![GitHub top language](https://img.shields.io/github/languages/top/ender-locke/eve-analytics)


**eve-analytics** is a Python package for parsing EVE Online combat logs and turning them into structured data and visual diagrams.

It helps you go from raw `.txt` logs → usable datasets → insights about fights, fleets, and pilot activity.

The package utilizing a SQLite DB to store log data and integrate Eve Online SDE.

---

## Features

* Parse EVE combat log files into structured data 
  * json & dfs
* Aggregate events like:
    * Damage (`dmg`)
    * Neutralizers / Nosferatu (`neut`, `nos`)
    * Repairs (`reps`, `cap_reps`)
    * Electronic warfare (`jams`, `scrams`)
    * Drones, reloads, links, and more
* Build datasets for analysis and visualization
* Designed to support diagram generation (fleet and pilot diagrams, timelines, etc.)

---

## Installation

```bash
pip install eve-analytics
```

## Quick Start

```python
from eve_analytics import EveAnalytics

ea = EveAnalytics(log_directory="/path/to/logs")
ea.parse_logs()
ea.load_db()
ea.generate_analytics('a_match_id')
ea.save_analytics(save_dir="/path/to/save")

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

## Error Handling

The package includes custom exceptions:

* `LogLocationError` — invalid directory path
* `LogDirectoryNotSetError` — parsing attempted without setting a directory
* `MissingSDEError` -- sde files are missing
* 

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
