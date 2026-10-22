import json
import os

images = [
    ("g1_001", 2, 5),
    ("g1_002", 3, 9),
    ("g1_003", 3, 5),
    ("g1_004", 4, 3),
    ("g1_005", 4, 5),
    ("g1_006", 4, 8),
    ("g1_007", 5, 3),
    ("g1_008", 5, 4),
    ("g1_009", 5, 7),
    ("g1_010", 5, 10),
    ("g1_011", 7, 4),
    ("g1_012", 7, 10),
    ("g1_013", 10, 5),
    ("g1_014", 10, 7),
    ("g1_015", 10, 9),
]

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
folder = os.path.join(project_root, "data", "gen1", "cr")

for img_id, rows, cols in images:
    filename = f"{img_id}_{rows}x{cols}_clean"
    data = {
        "image_id": img_id,
        "file_path": f"data/gen1/cr/{filename}.jpg",
        "source": "synthetic",
        "generation": 1,
        "parent_id": "real_001",
        "component_type": "CR",
        "grid_rows": rows,
        "grid_cols": cols,
        "total_defects": 0,
        "positions": [],
        "verified": False,
        "split": "",
        "prompt": "",
        "notes": "clean base, no defects"
    }
    path = os.path.join(folder, f"{filename}.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Created: {path}")