"""Unit matrix for the pure magic-byte sniffer (TEST-002, TEST-007).

``sniff_image_type(head: bytes) -> tuple[content_type, ext] | None`` is the security
primitive of US-2.3: it is *authoritative* (inspects only the leading bytes, never the
declared content-type or the client filename) and gates the allowlist (jpeg/png/webp).
The input-state matrix below (>= 6 cells) follows the fixed branch priority
(jpeg -> png -> webp -> None) and asserts the independence of the result from any
declared/extension input (which the function never receives).
"""

from __future__ import annotations

import pytest

from viridarium.domain.photo import sniff_image_type

pytestmark = pytest.mark.unit

_JPEG = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01"
_PNG = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
_WEBP = b"RIFF" + (32).to_bytes(4, "little") + b"WEBPVP8 " + b"\x00" * 8
_GIF = b"GIF89a" + b"\x00" * 8
_TEXT = b"hello world this is not an image"
_RIFF_NOT_WEBP = b"RIFF" + (32).to_bytes(4, "little") + b"AVI LIST" + b"\x00" * 8
_TRUNC_PNG = b"\x89PNG"


@pytest.mark.parametrize(
    ("case_id", "head", "expected"),
    [
        ("jpeg-sig", _JPEG, ("image/jpeg", "jpg")),
        ("png-sig", _PNG, ("image/png", "png")),
        ("webp-sig", _WEBP, ("image/webp", "webp")),
        ("gif-sig", _GIF, None),
        ("plain-text", _TEXT, None),
        ("empty", b"", None),
        ("riff-not-webp", _RIFF_NOT_WEBP, None),
        ("truncated-png", _TRUNC_PNG, None),
    ],
)
def test_sniff_image_type_matrix(
    case_id: str, head: bytes, expected: tuple[str, str] | None
) -> None:
    """Each signature cell maps to its allowlisted (ct, ext) or to ``None``."""
    assert sniff_image_type(head) == expected, case_id


def test_sniff_priority_jpeg_before_others() -> None:
    """A JPEG head returns jpeg (priority 1), not confused with later signatures."""
    assert sniff_image_type(_JPEG) == ("image/jpeg", "jpg")


def test_sniff_authoritative_over_declared_mismatch() -> None:
    """The function takes only bytes: a JPEG body always sniffs jpeg, a PNG body png,
    regardless of any declared type the caller may (wrongly) have. It never receives
    the declared type, documenting the contract that the caller cross-checks it."""
    assert sniff_image_type(_JPEG) == ("image/jpeg", "jpg")
    assert sniff_image_type(_PNG) == ("image/png", "png")


def test_sniff_riff_requires_webp_tag() -> None:
    """WEBP is gated on the ``WEBP`` tag at offset 8, not merely the ``RIFF`` prefix."""
    assert sniff_image_type(_WEBP) == ("image/webp", "webp")
    assert sniff_image_type(_RIFF_NOT_WEBP) is None
