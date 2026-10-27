"""Convert all non-.jpg images in a folder (default: 'dump') to .jpg format.

- Scans the target directory (resolves relative to project root)
- Converts non-.jpg image files to .jpg (quality=95, RGB mode)
- Deletes the original non-jpg files after successful conversion
- Skips files that are already .jpg
- Prints what it converted and what it skipped
- Resolves paths relative to project root so it can be run from anywhere

Usage:
    python 1_convert_to_jpg.py [folder_path]
"""

import sys
from pathlib import Path
from typing import Optional
from PIL import Image

# Supported image extensions recognized by Pillow
SUPPORTED_EXTENSIONS = {
    ext.lower()
    for ext, fmt in Image.registered_extensions().items()
    if fmt in Image.OPEN
}
SUPPORTED_EXTENSIONS.discard(".pdf")
SUPPORTED_EXTENSIONS.update({
    ".png", ".jpeg", ".jpg", ".webp", ".bmp", ".tiff", ".tif",
    ".gif", ".ico", ".jfif", ".avif", ".heic", ".heif"
})


def convert_images_in_folder(target_folder: Optional[Path] = None) -> None:
    project_root = Path(__file__).resolve().parent.parent

    if target_folder is None:
        if len(sys.argv) > 1:
            folder_path = Path(sys.argv[1].strip())
            target_folder = folder_path if folder_path.is_absolute() else (project_root / folder_path)
        else:
            target_folder = project_root / "dump"
    elif not target_folder.is_absolute():
        target_folder = project_root / target_folder

    print(f"Checking folder: {target_folder}")

    if not target_folder.exists():
        print(f"Folder does not exist at: {target_folder}")
        return

    items = sorted(target_folder.iterdir())
    if not items:
        print("No files found in the target folder.")
        return

    converted_count = 0
    skipped_count = 0
    error_count = 0

    for item in items:
        if item.is_dir():
            print(f"Skipped (directory): {item.name}")
            skipped_count += 1
            continue

        ext = item.suffix.lower()

        # Skip files that are already .jpg
        if ext == ".jpg":
            print(f"Skipped (already .jpg): {item.name}")
            skipped_count += 1
            continue

        # Skip non-image / unsupported files
        if ext not in SUPPORTED_EXTENSIONS:
            print(f"Skipped (non-image file): {item.name}")
            skipped_count += 1
            continue

        # Convert to .jpg
        dest_path = item.with_suffix(".jpg")
        try:
            with Image.open(item) as img:
                rgb_img = img.convert("RGB")
                rgb_img.save(dest_path, "JPEG", quality=95)

            # Delete original file only after successful save
            item.unlink()
            print(f"Converted: {item.name} -> {dest_path.name}")
            converted_count += 1
        except Exception as e:
            print(f"Error converting {item.name}: {e}")
            error_count += 1

    print(f"\nFinished: {converted_count} converted, {skipped_count} skipped, {error_count} errors.")


if __name__ == "__main__":
    convert_images_in_folder()
