"""
Local sample image paths for simulated recorded-document preview.

Place PNG files under sample_docs/ using the filenames in SAMPLE_DOCUMENT_IMAGE_FILENAMES
(keys are internal; values must match actual files on disk).
"""
from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SAMPLE_DOCS_DIR = PROJECT_ROOT / "sample_docs"

# document_type string (case-insensitive substring rules) -> filename under sample_docs/
SAMPLE_DOCUMENT_IMAGE_FILENAMES: dict[str, str] = {
    "mortgage": "mortgage.png",
    "warranty_deed": "warranty_deed.png",
    "release_of_lien": "release_of_lien.png",
    "mechanic_lien": "mechanic_lien.png",
    "quitclaim_deed": "quitclaim_deed.png",
}


def _sample_key_for_document_type(document_type: str) -> str | None:
    """Map a recorder document_type label to a SAMPLE_DOCUMENT_IMAGE_FILENAMES key."""
    dt = str(document_type or "").strip().lower()
    if not dt:
        return None
    if "quitclaim" in dt:
        return "quitclaim_deed"
    if "warranty" in dt and "deed" in dt:
        return "warranty_deed"
    if "mechanic" in dt:
        return "mechanic_lien"
    if "release" in dt and "lien" in dt:
        return "release_of_lien"
    if "mortgage" in dt and "satisfaction" not in dt:
        return "mortgage"
    return None


def resolve_sample_document_preview_image(document_type: str) -> Path | None:
    """
    Return the absolute path to a sample preview image if the type matches and the file exists.
    Otherwise None (caller shows generic placeholder).
    """
    key = _sample_key_for_document_type(document_type)
    if key is None:
        return None
    name = SAMPLE_DOCUMENT_IMAGE_FILENAMES.get(key)
    if not name:
        return None
    path = SAMPLE_DOCS_DIR / name
    if path.is_file():
        return path
    return None


def sample_document_placeholder_message(document_type: str) -> str:
    """Short message when no local sample file is available for this type."""
    if _sample_key_for_document_type(document_type) is None:
        return "No sample document mapping for this instrument type."
    return "Sample preview image not found in sample_docs for this instrument type."
