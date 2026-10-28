"""Move .jpg images from dump/ to target data/gen{N}/{component}/ folder
with a sequential naming prefix.

Workflow:
1. Copies the entire dump folder to a backup location at:
   D:\\downalods_D\\dump_backup_{timestamp}
2. Checks for duplicates against existing .jpg files in target folder:
   - NAME MATCH: stripped filename matches existing file's stripped name (skipped)
   - SIZE MATCH: file size in bytes matches existing file's size (skipped)
   - Use --force to skip duplicate checks and move all files regardless
3. Moves .jpg files to data/gen{N}/{component}/ with sequential prefix:
   {gen_prefix}_{seq:03d}_{original_filename}
4. Deletes only the moved .jpg files from dump/ (non-jpg files/folders remain untouched).
5. Prints a summary of files backed up, moved, skipped by name, skipped by size, deleted, and backup location.

Usage:
    python 2_move_from_dump.py <generation: g1|g2|g3|...> <component: cr|dsla> [--force]
    python 2_move_from_dump.py <target_folder_path> [--force]
"""

import re
import shutil
import sys
from datetime import datetime
from pathlib import Path


def strip_prefix(filename: str) -> str:
    """Strip generation prefix and sequence number (e.g. 'g2_001_' from 'g2_001_10x5_1bore(10r5c).jpg')."""
    m = re.match(r"^[a-zA-Z]\d+_\d+_(.*)$", filename)
    if m:
        return m.group(1)
    return filename


def main() -> None:
    # Resolve paths relative to project root (parent of scripts/) so it works from anywhere
    project_root = Path(__file__).resolve().parent.parent

    # Parse --force flag
    force_mode = "--force" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--force"]

    if len(args) == 1:
        # e.g. python 2_move_from_dump.py data/gen2/cr [--force]
        folder_path = Path(args[0].strip())
        target_folder = folder_path if folder_path.is_absolute() else (project_root / folder_path)
        comp_input = target_folder.name.lower()
        gen_input = target_folder.parent.name.lower()
    elif len(args) == 2:
        # e.g. python 2_move_from_dump.py g2 cr [--force]
        gen_input = args[0].strip()
        comp_input = args[1].strip().lower()

        gen_lower = gen_input.lower()
        if gen_lower.startswith("gen"):
            gen_folder = gen_lower
        elif gen_lower.startswith("g"):
            gen_folder = f"gen{gen_lower[1:]}"
        else:
            gen_folder = f"gen{gen_lower}"

        target_folder = project_root / "data" / gen_folder / comp_input
    else:
        print("Usage: python 2_move_from_dump.py <generation: g1|g2|g3|...> <component: cr|dsla> [--force]")
        print("   or: python 2_move_from_dump.py <target_folder_path> [--force]")
        sys.exit(1)

    # Parse generation prefix (e.g. "g2")
    gen_lower = gen_input.lower()
    if gen_lower.startswith("gen"):
        gen_prefix = f"g{gen_lower[3:]}"
    elif gen_lower.startswith("g"):
        gen_prefix = gen_lower
    else:
        gen_prefix = f"g{gen_lower}"

    dump_dir = project_root / "dump"

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
    target_folder.mkdir(parents=True, exist_ok=True)

    # Collect existing .jpg files in target folder for duplicate checks
    existing_info = []
    for ef in target_folder.iterdir():
        if ef.is_file() and ef.suffix.lower() == ".jpg":
            existing_info.append({
                "name": ef.name,
                "stripped_name": strip_prefix(ef.name),
                "size": ef.stat().st_size
            })

    # Determine the next sequential number based on existing files with same prefix
    pattern = re.compile(rf"^{re.escape(gen_prefix)}_(\d+)", re.IGNORECASE)
    existing_numbers = []
    for f in target_folder.iterdir():
        match = pattern.match(f.name)
        if match:
            existing_numbers.append(int(match.group(1)))

    next_seq = max(existing_numbers) + 1 if existing_numbers else 1

    if force_mode:
        print("FORCE MODE: skipping duplicate checks\n")

    # 2. Check duplicates and copy/move files
    moved_files = []
    skipped_by_name = 0
    skipped_by_size = 0

    for file in jpg_files:
        if not force_mode:
            # Check 1: NAME MATCH
            name_match = None
            for ef in existing_info:
                if ef["stripped_name"].lower() == file.name.lower():
                    name_match = ef
                    break

            if name_match:
                print(f"Skipped {file.name}: DUPLICATE NAME (matches {name_match['name']})")
                skipped_by_name += 1
                continue

            # Check 2: SIZE MATCH
            file_size = file.stat().st_size
            size_match = None
            for ef in existing_info:
                if ef["size"] == file_size:
                    size_match = ef
                    break

            if size_match:
                print(f"Skipped {file.name}: POTENTIAL DUPLICATE (same size as {size_match['name']})")
                skipped_by_size += 1
                continue
        else:
            file_size = file.stat().st_size

        new_filename = f"{gen_prefix}_{next_seq:03d}_{file.name}"
        dest_path = target_folder / new_filename

        shutil.copy2(file, dest_path)

        try:
            rel_dest = dest_path.relative_to(project_root)
        except ValueError:
            rel_dest = dest_path

        print(f"Moved: {file.name} -> {rel_dest}")

        moved_files.append((file, dest_path))
        # Keep existing_info updated for subsequent files in this batch
        existing_info.append({
            "name": new_filename,
            "stripped_name": file.name,
            "size": file_size
        })
        next_seq += 1

    moved_count = len(moved_files)

    # 3. After all files are successfully moved, delete only the moved .jpg files from dump
    deleted_count = 0
    for file, _ in moved_files:
        if file.exists() and file.is_file() and file.suffix.lower() == ".jpg":
            file.unlink()
            deleted_count += 1

    try:
        rel_target = target_folder.relative_to(project_root)
    except ValueError:
        rel_target = target_folder

    # 4. Print summary at the end
    print("\n--- Summary ---")
    print(f"- Target folder:           {rel_target}")
    print(f"- Files backed up:         {backed_up_count}")
    print(f"- Files moved:             {moved_count}")
    print(f"- Skipped by name:         {skipped_by_name}")
    print(f"- Skipped by size:         {skipped_by_size}")
    print(f"- Files deleted from dump: {deleted_count}")
    print(f"- Backup location:         {backup_dir}")


if __name__ == "__main__":
    main()
