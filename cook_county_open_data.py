"""
Cook County (IL) open data — minimal integration for the Streamlit prototype.

LIVE DATA MAPPING (source fields → app schema):
- Assessor - Parcel Sales: https://datacatalog.cookcountyil.gov/dataset/Assessor-Parcel-Sales/wvhk-k5uv
  - doc_no              → document_number (Clerk document number; see Clerk site for images)
  - sale_date           → recording_date (YYYY-MM-DD; assessor sale date, not Clerk “recorded” time)
  - seller_name         → grantor
  - buyer_name          → grantee
  - sale_price          → amount (formatted currency string to match mock UI)
  - pin                 → parcel_id (14-digit PIN, hyphenated for display)
  - mydec_deed_type / deed_type → document_type (best-effort → existing filter labels)
- Assessor - Parcel Addresses: https://datacatalog.cookcountyil.gov/dataset/Assessor-Parcel-Addresses/3723-97qp
  - pin (14-digit, same semantics as sales) → join key after `_normalize_pin_14` / `_coerce_pin_digits`
  - pin10 (first 10 digits) → secondary Socrata query only for PINs still missing after full-pin fetch
  - prop_address_*      → address (situs); mail_address_* → fallback when situs is blank

On HTTP errors, timeouts, or parse failures, callers should fall back to mock data (handled in app_v3).
"""

from __future__ import annotations

import json
import re
from datetime import date
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd

# Socrata SODA2 endpoints (Cook County Open Data / Assessor).
_PARCEL_SALES_RESOURCE = "https://datacatalog.cookcountyil.gov/resource/wvhk-k5uv.json"
_PARCEL_ADDRESSES_RESOURCE = "https://datacatalog.cookcountyil.gov/resource/3723-97qp.json"

_USER_AGENT = "MediciPrototype/1.0 (+https://datacatalog.cookcountyil.gov/)"
_TIMEOUT_SEC = 45
_SALES_LIMIT = 350
_ADDR_CHUNK = 40

# Shown on live rows when situs + mailing are blank or join misses (UI styles this in app_v3).
ADDRESS_UNAVAILABLE_LABEL = "Address not available in source data"
# Parcel Addresses has one row per PIN per tax year; a tiny $limit drops whole PINs from the response.
_ADDR_ROWS_PER_PIN_ESTIMATE = 50
_SODA_MAX_LIMIT = 50000


def _http_get_json(url: str, params: dict[str, str]) -> list[dict[str, Any]]:
    # Socrata query params use $-prefixed keys; keep $ unescaped.
    qs = urlencode(params)
    full = f"{url}?{qs}"
    req = Request(full, headers={"User-Agent": _USER_AGENT})
    with urlopen(req, timeout=_TIMEOUT_SEC) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    data = json.loads(raw)
    return data if isinstance(data, list) else []


def _coerce_pin_digits(pin: Any) -> str:
    """
    Normalize PIN-like values from Socrata (string, int, float).
    Leading zeros matter: int 1011000020000 → zfill(14) → correct Cook PIN.
    """
    if pin is None or pin == "":
        return ""
    if isinstance(pin, bool):
        return ""
    if isinstance(pin, float):
        if pin.is_integer():
            pin = int(pin)
        else:
            return re.sub(r"\D", "", str(pin))
    if isinstance(pin, int):
        s = str(pin)
        if len(s) > 14:
            return s[-14:] if s.isdigit() else ""
        return s.zfill(14) if s.isdigit() else ""
    digits = re.sub(r"\D", "", str(pin).strip())
    return digits.zfill(14) if digits else ""


def _normalize_pin_14(pin: Any) -> str:
    """14-digit canonical PIN for joins (sales ↔ addresses both publish full PIN)."""
    return _coerce_pin_digits(pin)


def resolved_live_address(addr_raw: str | None) -> str:
    """User-visible address line for live Cook rows; never a lone em dash when data is missing."""
    if addr_raw is None:
        return ADDRESS_UNAVAILABLE_LABEL
    s = str(addr_raw).strip()
    if not s or s == "—":
        return ADDRESS_UNAVAILABLE_LABEL
    return s


def format_cook_pin_display(pin: str | None) -> str:
    """14-digit Cook PIN → TT-SS-BBB-PPP-NNNN (display only)."""
    s = _normalize_pin_14(pin)
    if len(s) != 14:
        return (pin or "").strip() or "—"
    return f"{s[0:2]}-{s[2:4]}-{s[4:7]}-{s[7:10]}-{s[10:14]}"


def _map_document_type(mydec_deed_type: str | None, deed_type: str | None) -> str:
    """
    Map Assessor deed labels into the app’s fixed document_type vocabulary (search filters + tags).
    Best-effort only — Assessor categories do not match Recorder instrument types 1:1.
    """
    text = f"{mydec_deed_type or ''} {deed_type or ''}".lower()
    if "quit" in text:
        return "Quitclaim Deed"
    if "mortgage" in text or "deed of trust" in text:
        return "Mortgage"
    if "release" in text and "lien" in text:
        return "Release of Lien"
    if "satisfaction" in text or "reconveyance" in text:
        return "Satisfaction of Mortgage"
    if "mechanic" in text or "construction lien" in text:
        return "Mechanic Lien"
    if "warranty" in text or "trust" in text or "special warranty" in text:
        return "Warranty Deed"
    # Most arm’s-length transfers in this extract are deeds; keep UI consistent with filters.
    return "Warranty Deed"


def _format_currency_amount(sale_price: Any) -> str:
    if sale_price is None or sale_price == "":
        return "—"
    try:
        n = int(round(float(sale_price)))
        return f"${n:,}"
    except (TypeError, ValueError):
        return "—"


def _sale_date_iso(sale_date: str | None) -> str | None:
    if not sale_date:
        return None
    m = re.match(r"(\d{4}-\d{2}-\d{2})", str(sale_date))
    return m.group(1) if m else None


def _build_mailing_address(row: dict[str, Any]) -> str:
    """Fallback when situs fields are blank (Assessor notes situs can be missing)."""
    line = (row.get("mail_address_full") or row.get("mailing_address") or "").strip()
    city = (row.get("mail_address_city_name") or row.get("mailing_city") or "").strip()
    st = (row.get("mail_address_state") or row.get("mailing_state") or "").strip()
    z = (row.get("mail_address_zipcode_1") or row.get("mailing_zip") or "").strip()
    tail = ", ".join(p for p in (city, f"{st} {z}".strip()) if p)
    if line and tail:
        return f"{line}, {tail}"
    return line or tail or ""


def _build_situs_address(row: dict[str, Any]) -> str:
    """
    Prefer situs (property) columns from Parcel Addresses; fall back to mailing when situs is empty.
    API field names: prop_address_* and mail_address_* (see dataset column list).
    """
    line = (row.get("prop_address_full") or row.get("property_address") or "").strip()
    city = (row.get("prop_address_city_name") or row.get("property_city") or "").strip()
    st = (row.get("prop_address_state") or row.get("property_state") or "").strip()
    z = (row.get("prop_address_zipcode_1") or row.get("property_zip") or "").strip()
    tail = ", ".join(p for p in (city, f"{st} {z}".strip()) if p)
    if line and tail:
        situs = f"{line}, {tail}"
    else:
        situs = line or tail
    if situs:
        return situs
    mail = _build_mailing_address(row)
    return mail or "—"


def _merge_address_candidate(
    best: dict[str, tuple[int, str]],
    pin14: str,
    year: int,
    addr: str,
) -> None:
    if len(pin14) != 14 or not addr or addr == "—":
        return
    prev = best.get(pin14)
    if prev is None or year >= prev[0]:
        best[pin14] = (year, addr)


def _rows_from_address_query(where_clause: str, row_limit: int) -> list[dict[str, Any]]:
    params = {"$where": where_clause, "$limit": str(min(row_limit, _SODA_MAX_LIMIT))}
    try:
        return _http_get_json(_PARCEL_ADDRESSES_RESOURCE, params)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, OSError):
        return []


def _ingest_address_rows(rows: list[dict[str, Any]], best: dict[str, tuple[int, str]]) -> None:
    """Merge address API rows into best[canonical_pin14] using normalized full `pin` only."""
    for r in rows:
        pin = _normalize_pin_14(r.get("pin"))
        if len(pin) != 14:
            continue
        try:
            y = int(float(r.get("year") or r.get("tax_year") or 0))
        except (TypeError, ValueError):
            y = 0
        addr = _build_situs_address(r)
        _merge_address_candidate(best, pin, y, addr)


def _fetch_addresses_by_pin(pins: list[str]) -> dict[str, str]:
    """
    Latest tax year row per canonical 14-digit PIN → single display string.
    Join key: Parcel Sales `pin` and Parcel Addresses `pin` are both full PINs; values are normalized
    with the same zfill/int rules before querying or matching.
    """
    best: dict[str, tuple[int, str]] = {}
    normalized = []
    for p in pins:
        n = _normalize_pin_14(p)
        if len(n) == 14:
            normalized.append(n)
    if not normalized:
        return {}

    for i in range(0, len(normalized), _ADDR_CHUNK):
        chunk = normalized[i : i + _ADDR_CHUNK]
        in_list = ",".join("'" + p.replace("'", "''") + "'" for p in chunk)
        need_rows = len(chunk) * _ADDR_ROWS_PER_PIN_ESTIMATE
        row_limit = min(_SODA_MAX_LIMIT, max(5000, need_rows))
        rows = _rows_from_address_query(f"pin in({in_list})", row_limit)
        _ingest_address_rows(rows, best)

    # Second pass: PINs missing after truncated or failed chunk (cheap re-query with safe limit).
    missing = [p for p in normalized if p not in best or best[p][1] == "—"]
    if missing:
        for j in range(0, len(missing), 15):
            sub = missing[j : j + 15]
            in_list = ",".join("'" + p.replace("'", "''") + "'" for p in sub)
            rows = _rows_from_address_query(f"pin in({in_list})", min(_SODA_MAX_LIMIT, len(sub) * _ADDR_ROWS_PER_PIN_ESTIMATE))
            _ingest_address_rows(rows, best)

    # Third pass: query by pin10 for still-missing PINs, then keep only rows whose full pin matches
    # a sale PIN we need (handles rare cases where full-pin IN batches were incomplete).
    still = [p for p in normalized if p not in best or best[p][1] == "—"]
    if still:
        for k in range(0, len(still), 20):
            batch_pins = still[k : k + 20]
            pin10s = sorted({p[:10] for p in batch_pins if len(p) >= 10})
            if not pin10s:
                continue
            in10 = ",".join("'" + t.replace("'", "''") + "'" for t in pin10s)
            rows = _rows_from_address_query(
                f"pin10 in({in10})",
                min(_SODA_MAX_LIMIT, len(pin10s) * _ADDR_ROWS_PER_PIN_ESTIMATE * 4),
            )
            for r in rows:
                pin_full = _normalize_pin_14(r.get("pin"))
                if pin_full not in batch_pins:
                    continue
                try:
                    y = int(float(r.get("year") or 0))
                except (TypeError, ValueError):
                    y = 0
                addr = _build_situs_address(r)
                _merge_address_candidate(best, pin_full, y, addr)

    return {k: v[1] for k, v in best.items()}


def fetch_parcel_sales_raw(limit: int = _SALES_LIMIT) -> list[dict[str, Any]]:
    params = {"$order": "sale_date DESC", "$limit": str(limit)}
    return _http_get_json(_PARCEL_SALES_RESOURCE, params)


def load_cook_county_records_df() -> pd.DataFrame:
    """
    Return rows aligned with app_v3 `mock_results` columns (+ recording_date_dt).
    Empty DataFrame on any failure (caller merges with mock).
    """
    try:
        raw_rows = fetch_parcel_sales_raw()
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, OSError, ValueError):
        return pd.DataFrame()

    if not raw_rows:
        return pd.DataFrame()

    pins: list[str] = []
    seen_pin: set[str] = set()
    for r in raw_rows:
        p = _normalize_pin_14(r.get("pin"))
        if len(p) == 14 and p not in seen_pin:
            seen_pin.add(p)
            pins.append(p)
    addr_map = _fetch_addresses_by_pin(pins)

    out_rows: list[dict[str, Any]] = []
    seen_doc: set[str] = set()
    for r in raw_rows:
        pin_raw = r.get("pin")
        pin14 = _normalize_pin_14(pin_raw)
        parcel_disp = format_cook_pin_display(pin_raw)
        doc_no = str(r.get("doc_no") or "").strip()
        if not doc_no:
            doc_no = f"cook-row-{r.get('row_id', '')}".strip("-")
        if doc_no in seen_doc:
            continue
        seen_doc.add(doc_no)

        rec_iso = _sale_date_iso(r.get("sale_date"))
        if not rec_iso:
            continue
        try:
            rec_dt = date.fromisoformat(rec_iso)
        except ValueError:
            continue

        grantor = (r.get("seller_name") or "").strip() or "—"
        grantee = (r.get("buyer_name") or "").strip() or "—"
        party = f"{grantor} -> {grantee}"
        dtype = _map_document_type(r.get("mydec_deed_type"), r.get("deed_type"))
        addr_raw = addr_map.get(pin14) if len(pin14) == 14 else None
        addr = resolved_live_address(addr_raw)
        amount = _format_currency_amount(r.get("sale_price"))

        out_rows.append(
            {
                "document_number": doc_no,
                "document_type": dtype,
                "recording_date": rec_iso,
                "county": "Cook County",
                "party": party,
                "address_parcel": f"{addr} | PIN {parcel_disp}",
                "summary": "Cook County Assessor parcel sale (open data)",
                "grantor": grantor,
                "grantee": grantee,
                "address": addr,
                "parcel_id": parcel_disp,
                "amount": amount,
                "ai_summary": (
                    "Live row from Cook County Assessor open data (Parcel Sales + Parcel Addresses). "
                    "Sale date and parties come from the assessor extract; use the Clerk’s office for the "
                    "authoritative recorded instrument and scanned document."
                ),
                "key_insights": [
                    "Assessor sale extract — document type is a best-effort map from deed metadata (Cook County open data).",
                    "Consideration shown is the assessor sale price field, not necessarily the face of the deed (Cook County open data).",
                    "Situs address is from Parcel Addresses and may lag deed transfers (Cook County open data).",
                    "Use Clerk document number on the County Clerk site for official record detail (Cook County open data).",
                ],
                "recording_date_dt": rec_dt,
                # UI: distinguish from prototype mock rows (see app_v3 `data_source_display`).
                "data_source": "live_cook",
            }
        )

    if not out_rows:
        return pd.DataFrame()

    df = pd.DataFrame(out_rows)
    return df
