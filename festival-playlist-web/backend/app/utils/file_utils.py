import logging
import mimetypes
import os
import socket
from ipaddress import ip_address
from urllib.parse import urlparse

import httpx


logger = logging.getLogger(__name__)

ALLOWED_IMAGE_MIME_TYPES = {
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/webp",
    "image/gif",
}


async def read_image_url(image_url, max_bytes):
    url = _validate_image_url(image_url)

    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=httpx.Timeout(12.0, connect=5.0),
        max_redirects=3,
    ) as client:
        response = await client.get(url)

    if response.status_code >= 400:
        raise ValueError("Image URL could not be fetched")

    content_type = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    content_length = response.headers.get("content-length")

    if content_length and int(content_length) > max_bytes:
        raise ValueError("Remote image is too large")
    if content_type not in ALLOWED_IMAGE_MIME_TYPES:
        raise ValueError("Image URL must return a supported image type")
    if len(response.content) > max_bytes:
        raise ValueError("Remote image is too large")
    if not response.content:
        raise ValueError("Remote image is empty")

    return response.content, content_type


async def read_upload_file(upload, max_bytes):
    if not hasattr(upload, "read") or not hasattr(upload, "close"):
        raise ValueError("Uploaded file is invalid")

    content_type = getattr(upload, "content_type", None) or "application/octet-stream"
    filename = getattr(upload, "filename", "") or ""
    content_type = _normalize_content_type(filename, content_type)

    data = await upload.read()
    await upload.close()

    if not data:
        raise ValueError("Uploaded file is empty")
    if len(data) > max_bytes:
        raise ValueError("Uploaded file is too large")

    if _looks_like_image(filename, content_type):
        if content_type not in ALLOWED_IMAGE_MIME_TYPES:
            raise ValueError("Unsupported image type")

    return data, content_type


def safe_delete(path):
    if not path:
        return
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        logger.warning("Failed to delete temporary file")


def _looks_like_image(filename, content_type):
    lower = filename.lower()
    return content_type.startswith("image/") or lower.endswith((".png", ".jpg", ".jpeg", ".webp", ".gif"))


def _normalize_content_type(filename, content_type):
    if content_type and content_type != "application/octet-stream":
        return content_type
    guessed, _encoding = mimetypes.guess_type(filename)
    return guessed or content_type or "application/octet-stream"


def _validate_image_url(image_url):
    if not isinstance(image_url, str) or not image_url.strip():
        raise ValueError("image_url is required")

    url = image_url.strip()
    parsed = urlparse(url)
    if parsed.scheme not in ["http", "https"]:
        raise ValueError("Image URL must use http or https")
    if not parsed.hostname:
        raise ValueError("Image URL host is required")

    _reject_private_host(parsed.hostname)
    return url


def _reject_private_host(hostname):
    lower = hostname.lower()
    if lower in ["localhost", "localhost.localdomain"] or lower.endswith(".local"):
        raise ValueError("Private or local image URLs are not allowed")

    try:
        addresses = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        raise ValueError("Image URL host could not be resolved")

    for address in addresses:
        ip_text = address[4][0]
        parsed_ip = ip_address(ip_text)
        if (
            parsed_ip.is_private
            or parsed_ip.is_loopback
            or parsed_ip.is_link_local
            or parsed_ip.is_multicast
            or parsed_ip.is_reserved
            or parsed_ip.is_unspecified
        ):
            raise ValueError("Private or local image URLs are not allowed")
