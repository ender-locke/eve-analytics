import os
from io import BytesIO


def save_to_local(dfs: dict, date: str, base_path: str = "./combat_log_data"):
    """
    Saves multiple DataFrames as JSON files to a local folder:
    ./combat_log_data/<date>/<key>.json
    """

    # Build local directory: ./combat_log_data/date/
    output_dir = os.path.join(base_path, date)
    os.makedirs(output_dir, exist_ok=True)

    saved_files = []

    for key, df in dfs.items():
        # Convert dataframe to JSON string
        json_data = df.to_json(orient="records", indent=2)

        # Output filename
        filename = f"{key}.json"
        filepath = os.path.join(output_dir, filename)

        # Write JSON file
        with open(filepath, "w") as f:
            f.write(json_data)

        saved_files.append(filepath)
        print(f"Saved locally: {filepath}")

    return saved_files


def save_graph_local(fig, img_name, local_path):
    """
    Saves a matplotlib figure to a local path, mirroring the old GCS path.

    Example:
        save_graph_local(fig, "summary_graphs/2025-11-30/myplot.png")
        -> ./summary_graphs/2025-11-30/myplot.png
    """

    # Full path on disk
    full_path = os.path.join(local_path, f"{img_name}.png")

    # Ensure folders exist
    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    # Save figure as PNG
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)

    with open(full_path, "wb") as f:
        f.write(buf.read())

    print(f"📁 Graph saved locally: {full_path}")

    return full_path
