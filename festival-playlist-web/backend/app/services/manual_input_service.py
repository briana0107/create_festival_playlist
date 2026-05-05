import logging


logger = logging.getLogger(__name__)


def parse_manual_text(text, date=None):
    if not text.strip():
        raise ValueError("Manual input is empty")

    event_date = _nullable(date)
    seen = set()
    items = []

    for line in text.splitlines():
        artist_name = line.strip()
        if not artist_name:
            continue

        key = " ".join(artist_name.lower().split())
        if key in seen:
            continue
        seen.add(key)

        items.append(
            {
                "date": event_date,
                "day_label": None,
                "artist_name": artist_name,
                "stage": None,
                "start_time": None,
                "source_text": artist_name,
                "confidence": 1.0,
                "approved": True,
                "source": "manual",
            }
        )

    if not items:
        raise ValueError("No artist names found")

    return items


def _nullable(value):
    if value is None:
        return None
    text = str(value).strip()
    return text or None
