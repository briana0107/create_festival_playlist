import csv
import io
import logging


logger = logging.getLogger(__name__)


def parse_csv_bytes(csv_bytes):
    if not csv_bytes:
        raise ValueError("CSV file is empty")

    text = _decode_csv(csv_bytes)
    reader = csv.DictReader(io.StringIO(text))

    if not reader.fieldnames:
        raise ValueError("CSV header is required")

    items = []
    for row in reader:
        artist_name = _clean(row.get("artist_name"))
        if not artist_name:
            continue

        item = {
            "date": _nullable(row.get("date")),
            "day_label": _nullable(row.get("day_label")),
            "artist_name": artist_name,
            "stage": _nullable(row.get("stage")),
            "start_time": _nullable(row.get("start_time")),
            "source_text": _source_text(row),
            "confidence": 1.0,
            "approved": _parse_bool(row.get("approved"), True),
            "source": "csv",
        }
        items.append(item)

    if not items:
        raise ValueError("No artist_name values found in CSV")

    return items


def _decode_csv(csv_bytes):
    try:
        return csv_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            return csv_bytes.decode("cp949")
        except UnicodeDecodeError:
            raise ValueError("CSV must be UTF-8 or CP949 encoded")


def _clean(value):
    if value is None:
        return ""
    return str(value).strip()


def _nullable(value):
    cleaned = _clean(value)
    return cleaned if cleaned else None


def _parse_bool(value, default):
    if value is None or str(value).strip() == "":
        return default
    normalized = str(value).strip().lower()
    if normalized in ["true", "1", "yes", "y", "approved", "ok"]:
        return True
    if normalized in ["false", "0", "no", "n", "rejected", "x"]:
        return False
    return default


def _source_text(row):
    values = []
    for key in ["festival_name", "date", "day_label", "artist_name", "stage", "start_time"]:
        value = _clean(row.get(key))
        if value:
            values.append(value)
    return " | ".join(values)

