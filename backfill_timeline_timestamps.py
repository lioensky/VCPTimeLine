import argparse
import calendar
import os
import re
from pathlib import Path

TIMESTAMP_SIGNATURE_RE = re.compile(r"^\[\d{4}[-.]\d{1,2}[-.]\d{1,2}\]\s*-\s*.+\s*$")
MONTH_FILE_RE = re.compile(r"^(\d{4})-(\d{2})\.md$")


def get_character_name(timeline_dir: Path) -> str:
    """Infer character name from a '<character>timeline' directory name."""
    dir_name = timeline_dir.name
    if dir_name.endswith("timeline"):
        return dir_name[:-len("timeline")]
    return dir_name


def build_timestamp_signature(character_name: str, year: int, month: int) -> str:
    """Build '[YYYY-M-D] - character' using the last day of the target month."""
    last_day = calendar.monthrange(year, month)[1]
    return f"[{year}-{month}-{last_day}] - {character_name}"


def has_timestamp_signature(content: str) -> bool:
    """Return True if the first non-empty line is already a timestamp signature."""
    for line in content.splitlines():
        if not line.strip():
            continue
        return bool(TIMESTAMP_SIGNATURE_RE.match(line.strip()))
    return False


def backfill_file(file_path: Path, character_name: str, dry_run: bool = False) -> bool:
    """Prepend timestamp signature to one monthly timeline markdown file if missing."""
    match = MONTH_FILE_RE.match(file_path.name)
    if not match:
        return False

    year = int(match.group(1))
    month = int(match.group(2))
    content = file_path.read_text(encoding="utf-8")

    if has_timestamp_signature(content):
        return False

    timestamp_signature = build_timestamp_signature(character_name, year, month)
    new_content = f"{timestamp_signature}\n{content}"

    if not dry_run:
        file_path.write_text(new_content, encoding="utf-8")

    print(f"{'[DRY-RUN] ' if dry_run else ''}backfilled: {file_path} -> {timestamp_signature}")
    return True


def iter_timeline_dirs(base_dir: Path, selected_dirs: list[str] | None = None):
    """Yield timeline directories from selected paths or all '*timeline' directories."""
    if selected_dirs:
        for selected_dir in selected_dirs:
            timeline_dir = Path(selected_dir)
            if not timeline_dir.is_absolute():
                timeline_dir = base_dir / timeline_dir
            if timeline_dir.is_dir():
                yield timeline_dir
            else:
                print(f"skip missing directory: {timeline_dir}")
        return

    for child in base_dir.iterdir():
        if child.is_dir() and child.name.endswith("timeline"):
            yield child


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Backfill timestamp signatures for existing monthly timeline markdown files."
    )
    parser.add_argument(
        "timeline_dirs",
        nargs="*",
        help="Optional timeline directories to process. Defaults to all '*timeline' directories under current directory.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only print files that would be changed without writing changes.",
    )
    args = parser.parse_args()

    base_dir = Path.cwd()
    changed_count = 0

    for timeline_dir in iter_timeline_dirs(base_dir, args.timeline_dirs):
        character_name = get_character_name(timeline_dir)
        for file_path in sorted(timeline_dir.glob("*.md")):
            if backfill_file(file_path, character_name, args.dry_run):
                changed_count += 1

    print(f"done. backfilled files: {changed_count}")


if __name__ == "__main__":
    main()