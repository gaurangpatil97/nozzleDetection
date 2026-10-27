"""Generate metadata JSON files for .jpg images in a specified dataset folder.

Usage:
    python 3_create_jsons.py <folder_path>

Examples:
    python scripts/3_create_jsons.py data/gen2/cr     (from project root)
    python 3_create_jsons.py data/gen2/cr             (from scripts/)
"""

import json
import re
import sys
from pathlib import Path

# Mapping of defect keywords to dataset state names
STATE_MAP = {
    "full": "missing_full",
    "bore": "bore_defect",
}

# Mapping of folder names to component types
COMPONENT_MAP = {
    "cr": "CR",
    "dsla": "DSLA",
}


def parse_filename(stem: str, folder_name: str, rel_file_path: str) -> dict:
    # 1. image_id (first two underscore-separated parts, e.g. "g2_001")
    parts = stem.split("_")
    if len(parts) >= 2:
        image_id = f"{parts[0]}_{parts[1]}"
    else:
        image_id = stem

    # 2. generation (e.g. "g1" -> 1, "g2" -> 2)
    gen_match = re.search(r"g(\d+)", parts[0], re.IGNORECASE)
    generation = int(gen_match.group(1)) if gen_match else 0

    # 3. grid (e.g. "10x5" -> rows=10, cols=5)
    grid_match = re.search(r"(\d+)x(\d+)", stem)
    if grid_match:
        grid_rows = int(grid_match.group(1))
        grid_cols = int(grid_match.group(2))
    else:
        grid_rows = 0
        grid_cols = 0

    # 4. component_type derived from folder name ("cr" -> "CR", "dsla" -> "DSLA")
    component_type = COMPONENT_MAP.get(folder_name.lower(), folder_name.upper())

    # 5. Parse defects and positions
    positions = []
    # If defect part is clean: total_defects=0, positions=[]
    if "clean" in stem.lower() and "(" not in stem:
        total_defects = 0
    else:
        # Match each defect group, e.g. "2full(2r3c, 3r3c)" or "1bore(5r2c)"
        group_pattern = re.compile(r"(full|bore)\s*\(([^)]+)\)", re.IGNORECASE)
        for match in group_pattern.finditer(stem):
            defect_type = match.group(1).lower()
            state = STATE_MAP.get(defect_type, defect_type)
            pos_str = match.group(2)

            # Positions are in format "XrYc" (e.g. 10r5c -> row 10, col 5)
            pos_pattern = re.compile(r"(\d+)r(\d+)c", re.IGNORECASE)
            for pos_match in pos_pattern.finditer(pos_str):
                row = int(pos_match.group(1))
                col = int(pos_match.group(2))
                positions.append({
                    "row": row,
                    "col": col,
                    "state": state
                })

        total_defects = len(positions)

    return {
        "image_id": image_id,
        "file_path": rel_file_path,
        "source": "synthetic",
        "generation": generation,
        "parent_id": None,
        "component_type": component_type,
        "grid_rows": grid_rows,
        "grid_cols": grid_cols,
        "total_defects": total_defects,
        "positions": positions,
        "verified": False,
        "split": "",
        "prompt": "",
        "notes": ""
    }


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python 3_create_jsons.py <folder_path>")
        sys.exit(1)

    # Resolve paths relative to project root (parent of scripts/) so running from anywhere works
    project_root = Path(__file__).resolve().parent.parent
    folder_path = Path(sys.argv[1].strip())
    target_folder = folder_path if folder_path.is_absolute() else (project_root / folder_path)

    if not target_folder.exists() or not target_folder.is_dir():
        print(f"Folder not found: {target_folder}")
        sys.exit(1)

    jpg_files = sorted([
        f for f in target_folder.iterdir()
        if f.is_file() and f.suffix.lower() == ".jpg"
    ])

    if not jpg_files:
        print(f"No .jpg files found in: {target_folder}")
        return

    created_count = 0
    skipped_count = 0

    folder_name = target_folder.name

    for jpg_file in jpg_files:
        json_path = jpg_file.with_suffix(".json")

        # Skip if matching .json already exists
        if json_path.exists():
            print(f"Skipped (exists): {json_path.name}")
            skipped_count += 1
            continue

        # Relative path from project root using forward slashes
        try:
            rel_file_path = jpg_file.relative_to(project_root).as_posix()
        except ValueError:
            rel_file_path = jpg_file.as_posix()

        # Parse filename and build JSON data
        data = parse_filename(jpg_file.stem, folder_name, rel_file_path)

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        print(f"Created: {json_path.name}")
        created_count += 1

    print(f"\nDone. Created: {created_count}, Skipped: {skipped_count}")


if __name__ == "__main__":
    main()
