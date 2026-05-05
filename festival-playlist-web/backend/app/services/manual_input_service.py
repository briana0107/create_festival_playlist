import logging


logger = logging.getLogger(__name__)


def parse_manual_text(text):
    if not text.strip():
        raise ValueError("Manual input is empty")

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
                "date": None,
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

