import base64
import json
import logging
import os

from openai import OpenAI


logger = logging.getLogger(__name__)


def extract_lineup_from_poster(api_key, image_bytes, mime_type, festival_name):
    if not api_key:
        raise ValueError("OpenAI API key is required")
    if not image_bytes:
        raise ValueError("Poster image is empty")

    client = OpenAI(api_key=api_key)
    model = os.getenv("OPENAI_VISION_MODEL", "gpt-4.1-mini")
    image_data = base64.b64encode(image_bytes).decode("ascii")
    image_url = "data:%s;base64,%s" % (mime_type, image_data)

    response = client.responses.create(
        model=model,
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": _prompt(festival_name)},
                    {"type": "input_image", "image_url": image_url, "detail": "high"},
                ],
            }
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "festival_lineup_extraction",
                "strict": True,
                "schema": _lineup_schema(),
            }
        },
    )

    raw_text = response.output_text
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError:
        logger.error("OpenAI response was not valid JSON")
        raise ValueError("OpenAI response was not valid JSON")

    items = data.get("items", [])
    if not isinstance(items, list):
        raise ValueError("OpenAI response did not include an items list")

    return [_normalize_poster_item(item) for item in items if _has_artist(item)]


def _prompt(festival_name):
    festival_line = "Festival name: %s" % festival_name if festival_name else "Festival name: unknown"
    return """
You extract music festival lineup information from a poster image.

Return JSON only, matching the provided schema.

Rules:
- Extract artist or performer names only.
- Exclude sponsors, venue names, ticketing text, staff, booth names, generic labels, and social media copy.
- Preserve visible Korean, Japanese, English, and mixed-language artist names.
- If date, day label, stage, or start time is visible, structure it as much as possible.
- date must be YYYY-MM-DD if the full date is visible or confidently inferable from the poster; otherwise null.
- start_time must be HH:mm in 24-hour time if visible; otherwise null.
- source_text should contain the raw visible text that caused the extraction.
- confidence is 0.0 to 1.0 based on visual certainty.
- approved should default to true.
- source must be "poster".

%s
""" % festival_line


def _lineup_schema():
    nullable_string = {"anyOf": [{"type": "string"}, {"type": "null"}]}
    return {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "date": nullable_string,
                        "day_label": nullable_string,
                        "artist_name": {"type": "string"},
                        "stage": nullable_string,
                        "start_time": nullable_string,
                        "source_text": {"type": "string"},
                        "confidence": {"type": "number"},
                        "approved": {"type": "boolean"},
                        "source": {"type": "string", "enum": ["poster"]},
                    },
                    "required": [
                        "date",
                        "day_label",
                        "artist_name",
                        "stage",
                        "start_time",
                        "source_text",
                        "confidence",
                        "approved",
                        "source",
                    ],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["items"],
        "additionalProperties": False,
    }


def _has_artist(item):
    return isinstance(item, dict) and str(item.get("artist_name") or "").strip()


def _normalize_poster_item(item):
    return {
        "date": _nullable(item.get("date")),
        "day_label": _nullable(item.get("day_label")),
        "artist_name": str(item.get("artist_name") or "").strip(),
        "stage": _nullable(item.get("stage")),
        "start_time": _nullable(item.get("start_time")),
        "source_text": str(item.get("source_text") or item.get("artist_name") or "").strip(),
        "confidence": _confidence(item.get("confidence")),
        "approved": bool(item.get("approved", True)),
        "source": "poster",
    }


def _nullable(value):
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in ["null", "none", "unknown", "n/a"]:
        return None
    return text


def _confidence(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, number))

