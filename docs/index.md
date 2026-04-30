# Welcome to EveAnalytics
I am not affiliated with ccp, please use this with respect to their infrastructure

## Introduction
**eve-analytics** is a Python package for parsing EVE Online combat logs and turning them into structured data and visual diagrams.

It helps you go from raw `.txt` logs → usable datasets → insights about fights, fleets, and pilot activity.

The package utilizing a SQLite DB to store log data and integrate Eve Online SDE.

This is currently a work in progress

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

## Links
[EveAnalytics Github](https://github.com/ender-locke/eve-analytics)

[pypi](https://pypi.org/project/eve-analytics/)

