"""Regenerate data/nozzle_detection_tracker.csv from JSON metadata files across generations.

Usage:
    python 5_regenerate_csv.py <component: cr|dsla>

Example:
    python scripts/5_regenerate_csv.py cr
"""

import csv
import json
import re
import sys
from pathlib import Path


HEADERS = [
    "image_id",
    "file_path",
    "source",
    "gen",
    "parent",
    "component",
    "rows",
    "cols",
    "total_defects",
    "defects",
    "defects_present",
    "reviewed",
    "finalized",
    "split",
    "notes"
]


def get_state_short(state: str) -> str:
    if not state:
        return ""
    state_lower = str(state).lower()
    if "full" in state_lower:
        return "full"
    if "bore" in state_lower:
        return "bore"
    return state_lower


def format_defects(total_defects: int, positions: list) -> str:
    if total_defects == 0 or not positions:
        return "clean"

    parts = []
    for pos in positions:
        if not isinstance(pos, dict):
            continue
        row = pos.get("row")
        col = pos.get("col")
        st = get_state_short(pos.get("state", ""))

        if row is not None and col is not None:
            parts.append(f"r{row}c{col}:{st}")
        elif row is not None:
            parts.append(f"r{row}:{st}")
        elif col is not None:
            parts.append(f"c{col}:{st}")
        else:
            parts.append(st)

    return " ".join(parts) if parts else "clean"


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python 5_regenerate_csv.py <component: cr|dsla>")
        sys.exit(1)

    component_arg = sys.argv[1].strip().lower()

    # Resolve paths relative to script location so it works from anywhere
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data"
    csv_path = data_dir / "nozzle_detection_tracker.csv"

    # Identify candidate folders for the specified component
    candidate_folders = []

    # 1. Real folder: data/real/{component}/
    real_folder = data_dir / "real" / component_arg
    if real_folder.is_dir():
        candidate_folders.append(real_folder)

    # 2. Gen folders: data/gen*/{component}/ sorted numerically (gen1, gen2, gen3, ...)
    gen_folders = [
        d / component_arg
        for d in data_dir.iterdir()
        if d.is_dir() and re.match(r"^gen\d+$", d.name, re.IGNORECASE) and (d / component_arg).is_dir()
    ]
    gen_folders.sort(key=lambda p: int(re.search(r"\d+", p.parent.name).group(0)))
    candidate_folders.extend(gen_folders)

    if not candidate_folders:
        print(f"No folders found for component '{component_arg}' in {data_dir}")
        sys.exit(1)

    rows = []
    folder_counts = {}

    for folder in candidate_folders:
        try:
            rel_folder = folder.relative_to(project_root).as_posix()
        except ValueError:
            rel_folder = folder.as_posix()

        json_files = sorted(folder.glob("*.json"))
        count = 0

        for json_path in json_files:
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                print(f"Warning: Failed to read {json_path}: {e}")
                continue

            image_id = str(data.get("image_id", ""))
            file_path = str(data.get("file_path", ""))
            source = str(data.get("source", ""))
            gen = data.get("generation", 0)

            parent_id = data.get("parent_id")
            parent = "-" if parent_id is None or str(parent_id).strip() == "" else str(parent_id)

            component = str(data.get("component_type", ""))
            rows_val = "" if data.get("grid_rows") is None else data.get("grid_rows")
            cols_val = "" if data.get("grid_cols") is None else data.get("grid_cols")

            total_defects = int(data.get("total_defects", 0))
            positions = data.get("positions", [])
            defects_str = format_defects(total_defects, positions)

            defects_present = "T" if total_defects > 0 else "F"
            reviewed = "T" if bool(data.get("verified")) else "F"
            finalized = reviewed  # same as reviewed for now

            split = str(data.get("split", "") or "")
            notes = str(data.get("notes", "") or "")

            row = {
                "image_id": image_id,
                "file_path": file_path,
                "source": source,
                "gen": gen,
                "parent": parent,
                "component": component,
                "rows": rows_val,
                "cols": cols_val,
                "total_defects": total_defects,
                "defects": defects_str,
                "defects_present": defects_present,
                "reviewed": reviewed,
                "finalized": finalized,
                "split": split,
                "notes": notes
            }
            rows.append(row)
            count += 1

        folder_counts[rel_folder] = count

    # Sort rows by generation (0 first, then 1, 2, ...), then by image_id
    def sort_key(r):
        gen_val = r["gen"]
        if not isinstance(gen_val, int):
            try:
                gen_val = int(gen_val)
            except (ValueError, TypeError):
                gen_val = 999
        return (gen_val, str(r["image_id"]))

    rows.sort(key=sort_key)

    # Overwrite CSV completely
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS)
        writer.writeheader()
        writer.writerows(rows)

    try:
        rel_csv = csv_path.relative_to(project_root).as_posix()
    except ValueError:
        rel_csv = csv_path.as_posix()

    print(f"Successfully generated tracker CSV: {rel_csv}\n")
    print("--- Summary ---")
    for f_path, c in folder_counts.items():
        print(f"- {f_path}: {c} row(s)")
    print(f"Total rows written: {len(rows)}")


if __name__ == "__main__":
    main()
