import calendar
import os
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent

def get_timeline_dir(character_name: str) -> str:
    """Returns the absolute timeline directory path for a character, creating it if needed."""
    dir_path = PROJECT_DIR / f"{character_name}timeline"
    dir_path.mkdir(parents=True, exist_ok=True)
    return str(dir_path)

def get_summarized_months(character_name: str, start_ym: str, end_ym: str) -> set:
    """Returns a set of YYYY-MM strings that already have markdown files."""
    dir_name = get_timeline_dir(character_name)
    existing_months = set()
    for f in os.listdir(dir_name):
        if f.endswith(".md"):
            ym = f.replace(".md", "")
            if start_ym <= ym <= end_ym:
                existing_months.add(ym)
    return existing_months

def save_month_summary(character_name: str, ym: str, content: str):
    """Saves the summary content to the character's timeline directory."""
    dir_name = get_timeline_dir(character_name)
    file_path = os.path.join(dir_name, f"{ym}.md")
    
    # Prepend the database-compatible timestamp signature and title
    year, month = ym.split("-")
    last_day = calendar.monthrange(int(year), int(month))[1]
    timestamp_signature = f"[{int(year)}-{int(month)}-{last_day}] - {character_name}\n"
    title = f"# {year}年{month}月{character_name}时间线\n\n"
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(timestamp_signature + title + content)
