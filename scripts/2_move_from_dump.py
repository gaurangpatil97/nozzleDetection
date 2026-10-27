"""Move .jpg images from dump/ to target data/gen{N}/{component}/ folder
with a sequential naming prefix.

Workflow:
1. Copies the entire dump folder to a backup location at:
   D:\\downalods_D\\dump_backup_{timestamp}
2. Moves .jpg files to data/gen{N}/{component}/ with sequential prefix:
   {gen_prefix}_{seq:03d}_{original_filename}
3. Deletes only the moved .jpg files from dump/ (non-jpg files/folders remain untouched).
4. Prints a summary of files backed up, moved, deleted, and backup location.

Usage:
    python move_from_dump.py <generation: g1|g2|g3|...> <component: cr|dsla>
"""

import re
import shutil
import sys
from datetime import datetime
from pathlib import Path


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: python move_from_dump.py <generation: g1|g2|g3|...> <component: cr|dsla>")
        sys.exit(1)

    gen_input = sys.argv[1].strip()
    comp_input = sys.argv[2].strip().lower()

    # Parse generation prefix and folder (e.g. g2 -> folder: gen2, prefix: g2)
    gen_lower = gen_input.lower()
    if gen_lower.startswith("gen"):
        gen_num = gen_lower[3:]
        gen_prefix = f"g{gen_num}"
        gen_folder = f"gen{gen_num}"
    elif gen_lower.startswith("g"):
        gen_num = gen_lower[1:]
        gen_prefix = gen_lower
        gen_folder = f"gen{gen_num}"
    else:
        gen_prefix = f"g{gen_lower}"
        gen_folder = f"gen{gen_lower}"

    # Resolve paths relative to script location so it works from anywhere
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    dump_dir = project_root / "dump"
    target_dir = project_root / "data" / gen_folder / comp_input

    if not dump_dir.exists():
        print(f"Dump folder does not exist at: {dump_dir}")
        return

    # Find only .jpg files (ignore non-jpg files, folders, zip files)
    jpg_files = sorted([
        f for f in dump_dir.iterdir()
        if f.is_file() and f.suffix.lower() == ".jpg"
    ])

    if not jpg_files:
        print("No .jpg files found in dump folder.")
        return

    # 1. Backup entire dump folder before moving any files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_base = Path(r"D:\downalods_D")
    backup_dir = backup_base / f"dump_backup_{timestamp}"
    backup_base.mkdir(parents=True, exist_ok=True)

    print(f"Backing up dump folder to: {backup_dir}")
    shutil.copytree(dump_dir, backup_dir, dirs_exist_ok=True)
    backed_up_count = sum(1 for f in backup_dir.rglob("*") if f.is_file())
    print(f"Backup created successfully: {backed_up_count} file(s) backed up.\n")

    # Ensure target directory exists
    target_dir.mkdir(parents=True, exist_ok=True)

    # Determine the next sequential number based on existing files with same prefix
    pattern = re.compile(rf"^{re.escape(gen_prefix)}_(\d+)", re.IGNORECASE)
    existing_numbers = []
    for f in target_dir.iterdir():
        match = pattern.match(f.name)
        if match:
            existing_numbers.append(int(match.group(1)))

    next_seq = max(existing_numbers) + 1 if existing_numbers else 1

    # 2. Copy/move each .jpg file with sequential prefix
    moved_files = []
    for file in jpg_files:
        new_filename = f"{gen_prefix}_{next_seq:03d}_{file.name}"
        dest_path = target_dir / new_filename

        shutil.copy2(file, dest_path)

        rel_dest = dest_path.relative_to(project_root)
        print(f"Moved: {file.name} -> {rel_dest}")

        moved_files.append((file, dest_path))
        next_seq += 1

    moved_count = len(moved_files)

    # 3. After all files are successfully moved, delete only the moved .jpg files from dump
    deleted_count = 0
    for file, _ in moved_files:
        if file.exists() and file.is_file() and file.suffix.lower() == ".jpg":
            file.unlink()
            deleted_count += 1

    # 4. Print summary at the end
    print("\n--- Summary ---")
    print(f"- Files backed up:         {backed_up_count}")
    print(f"- Files moved:             {moved_count}")
    print(f"- Files deleted from dump: {deleted_count}")
    print(f"- Backup location:         {backup_dir}")


if __name__ == "__main__":
    main()
