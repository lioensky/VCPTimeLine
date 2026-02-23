import os
import re
from collections import defaultdict
import config

# Regex matches: [2026-02-22] - Nova or 2025.05.14.3-小吉
# Group 1: Year (4 digits)
# Group 2: Month (1-2 digits)
# Group 3: Day (1-2 digits)
# Group 4: Signature (author)
HEADER_PATTERN = re.compile(r"^\[?\s*(\d{4})[\.\-](\d{1,2})[\.\-](\d{1,2})(?:\.\d+)?\s*\]?\s*-\s*(.+?)\s*$")

def parse_first_line(file_path):
    """
    Read the first line of a file, trying utf-8 then gbk.
    Returns (year, month, author) or None if not matching.
    """
    first_line = ""
    for encoding in ['utf-8', 'gbk', 'gb18030']:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                first_line = f.readline().strip()
                # Also skip empty lines at the very beginning if any (optional, but requested format is first line)
                while not first_line:
                    line = f.readline()
                    if not line: # EOF
                        break
                    first_line = line.strip()
                break
        except UnicodeDecodeError:
            continue
        except Exception:
            return None
            
    if not first_line:
        return None
        
    match = HEADER_PATTERN.match(first_line)
    if match:
        year = match.group(1)
        month = match.group(2).zfill(2) # Ensure 2-digit month
        author = match.group(4).strip()
        return year, month, author
    return None

def should_ignore_dir(dir_path):
    parts = os.path.normpath(dir_path).split(os.sep)
    for ignore in config.IGNORE_FOLDERS:
        if ignore in parts:
            return True
    return False

def discover_memories(character_name, start_year_month, end_year_month):
    """
    TraverseMEMORY_BASE_PATH, filter by date and character, read contents.
    start_year_month, end_year_month format: "YYYY-MM"
    Return dictionary: { "YYYY-MM": [memory_content1, memory_content2, ...] }
    """
    memories_by_month = defaultdict(list)
    base_path = config.MEMORY_BASE_PATH
    
    if not os.path.exists(base_path):
        raise ValueError(f"Memory base path does not exist: {base_path}")

    start_ym = start_year_month.strip()
    end_ym = end_year_month.strip()

    for root, dirs, files in os.walk(base_path):
        # Filter directories in-place to avoid parsing ignored folders
        dirs[:] = [d for d in dirs if not should_ignore_dir(os.path.join(root, d))]
        
        for file in files:
            if file.lower().endswith(('.txt', '.md')):
                file_path = os.path.join(root, file)
                
                parsed = parse_first_line(file_path)
                if parsed:
                    year, month, author = parsed
                    if author == character_name:
                        ym = f"{year}-{month}"
                        if start_ym <= ym <= end_ym:
                            # Read full content
                            try:
                                for enc in ['utf-8', 'gbk', 'gb18030']:
                                    try:
                                        with open(file_path, 'r', encoding=enc) as f:
                                            # Skip the first non-empty line (the header)
                                            lines = f.readlines()
                                            
                                            content_lines = []
                                            found_header = False
                                            for line in lines:
                                                if not found_header and line.strip():
                                                    found_header = True
                                                    continue # Skip header
                                                content_lines.append(line)
                                                
                                            content = "".join(content_lines).strip()
                                            if content:
                                                memories_by_month[ym].append(content)
                                        break
                                    except UnicodeDecodeError:
                                        pass
                            except Exception as e:
                                print(f"Error reading file {file_path}: {e}")
                                
    return memories_by_month
