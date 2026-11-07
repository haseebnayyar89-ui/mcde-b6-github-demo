"""Task 09 | Streaming Log Inspector
Line format: YYYY-MM-DD HH:MM:SS | LEVEL | message
"""
from datetime import datetime


def parse_line(line):
    """Return (timestamp, level, message) or None if the line is malformed."""
    parts = line.split(" | ", 2)
    if len(parts) != 3:
        return None
    timestamp, level, message = parts[0].strip(), parts[1].strip(), parts[2].strip()
    try:
        datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None
    if not level.isalpha() or not level.isupper() or message == "":
        return None
    return timestamp, level, message


def read_errors(path, stats=None):
    """Generator: reads one line at a time and yields only ERROR records.
    Pass a dictionary as stats to get the number of malformed lines."""
    if stats is None:
        stats = {}
    stats["malformed"] = 0
    with open(path, "r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):   # file is read line by line
            line = line.rstrip("\n")
            if line.strip() == "":
                continue
            parsed = parse_line(line)
            if parsed is None:
                stats["malformed"] += 1
                continue
            timestamp, level, message = parsed
            if level == "ERROR":
                yield (line_number, timestamp, message)


def summarize_errors(path):
    """Return (errors_per_date, malformed_count)."""
    stats = {}
    per_date = {}
    for line_number, timestamp, message in read_errors(path, stats):
        date = timestamp[:10]
        per_date[date] = per_date.get(date, 0) + 1
    return per_date, stats["malformed"]


def create_sample_log(path):
    lines = [
        "2026-11-07 10:30:00 | ERROR | Connection lost",
        "2026-11-07 10:31:12 | INFO | Reconnected",
        "this line is not valid",
        "2026-11-07 11:00:00 | ERROR | Disk almost full",
        "2026-13-45 99:99:99 | ERROR | Bad timestamp",
        "2026-11-08 09:20:00 | ERROR | Timeout",
    ]
    with open(path, "w", encoding="utf-8") as file:
        file.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    create_sample_log("sample_app.log")
    for record in read_errors("sample_app.log"):
        print(record)
    print(summarize_errors("sample_app.log"))
