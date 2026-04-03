"""
Normalize raw API responses into a unified contract format.

Each normalizer takes a list of raw records from its respective API
and returns a list of dicts with the standard contract schema.
"""

import hashlib
import logging
from datetime import date

logger = logging.getLogger(__name__)


def is_active(result: dict) -> bool:
    """Return True if the contract is still open/active.
    This is the source-of-truth check applied to ALL results regardless of API.
    """
    today = date.today().isoformat()

    status_val = (result.get("status") or "").lower()

    # Explicitly inactive statuses
    if status_val in ("closed", "completed", "cancelled", "expired", "awarded"):
        return False

    # If close/response date has passed, exclude it
    close_date = result.get("close_date")
    if close_date and close_date < today:
        return False

    return True


def _safe_float(value) -> float | None:
    if value is None:
        return None
    try:
        return float(str(value).replace(",", "").replace("$", "").strip())
    except (ValueError, TypeError):
        return None


def _safe_str(value) -> str | None:
    if value is None or value == "":
        return None
    return str(value).strip()


def _make_id(source: str, *parts) -> str:
    raw = f"{source}:{'|'.join(str(p) for p in parts)}"
    return hashlib.md5(raw.encode()).hexdigest()


def _canadabuys_url(record: dict) -> str | None:
    """Build a CanadaBuys detail page URL from a record.

    CanadaBuys detail pages use the pattern:
      canadabuys.canada.ca/en/tender-opportunities/tender-notice/{referenceNumber}
    The referenceNumber is a slug like 'ws5145816815-doc5146035583' (case-insensitive).

    We check multiple fields that might contain it:
      - reference_number (the full slug, e.g. WS5145816815-Doc5146035583)
      - referenceNumber (alternate casing)
    If only a solicitation_number is available, it won't resolve to a detail page
    so we skip it rather than link to a broken URL.
    """
    ref = (
        record.get("reference_number")
        or record.get("referenceNumber")
        or record.get("ref_number")
    )
    if ref:
        return f"https://canadabuys.canada.ca/en/tender-opportunities/tender-notice/{ref.lower()}"
    return None


def _map_procuredata_status(record: dict) -> str:
    raw = (record.get("status") or record.get("tender_status") or "").lower()
    if raw in ("open", "active"):
        return "active"
    if raw in ("closed", "completed"):
        return "closed"
    if raw in ("cancelled",):
        return "cancelled"
    if raw in ("awarded",):
        return "awarded"
    return "unknown"


def normalize_procuredata(records: list[dict]) -> list[dict]:
    results = []
    for r in records:
        try:
            entry = {
                "id": _make_id("procuredata", r.get("record_id", r.get("id", r.get("title_en", "")))),
                "title": _safe_str(r.get("title_en")) or _safe_str(r.get("title")) or "Untitled",
                "description": _safe_str(r.get("description_en")) or _safe_str(r.get("description")) or "",
                "value": _safe_float(r.get("contract_value") or r.get("value")),
                "currency": "CAD",
                "awarded_date": _safe_str(r.get("award_date") or r.get("date")),
                "close_date": _safe_str(r.get("closing_date")),
                "vendor": _safe_str(r.get("vendor_name") or r.get("vendor")),
                "department": _safe_str(r.get("department_en") or r.get("department")) or "Unknown",
                "country": "CA",
                "source": "procuredata",
                "url": _safe_str(r.get("url"))
                    or _canadabuys_url(r),
                "status": _map_procuredata_status(r),
            }
            entry["is_active"] = is_active(entry)
            results.append(entry)
        except Exception as e:
            logger.warning("ProcureData normalize error: %s", e)
    return results


def _map_open_canada_status(record: dict) -> str:
    raw = (record.get("contract_status") or record.get("status") or "").lower()
    if raw in ("active", "open", "in progress"):
        return "active"
    if raw in ("closed", "completed", "complete"):
        return "closed"
    if raw in ("cancelled",):
        return "cancelled"
    if raw in ("awarded",):
        return "awarded"
    # If delivery_date is in the past, likely completed
    delivery = record.get("delivery_date") or ""
    if delivery and delivery < date.today().isoformat():
        return "closed"
    return "unknown"


def normalize_open_canada(records: list[dict]) -> list[dict]:
    results = []
    for r in records:
        try:
            entry = {
                "id": _make_id("open_canada", r.get("_id", r.get("reference_number", ""))),
                "title": _safe_str(r.get("description_en")) or _safe_str(r.get("description")) or "Untitled",
                "description": _safe_str(r.get("comments_en")) or _safe_str(r.get("additional_comments_en")) or "",
                "value": _safe_float(r.get("contract_value") or r.get("original_value")),
                "currency": "CAD",
                "awarded_date": _safe_str(r.get("award_date") or r.get("contract_date")),
                "close_date": _safe_str(r.get("delivery_date")),
                "vendor": _safe_str(r.get("vendor_name")),
                "department": _safe_str(r.get("owner_org") or r.get("owner_org_title")) or "Unknown",
                "country": "CA",
                "source": "open_canada",
                "url": _canadabuys_url(r),
                "status": _map_open_canada_status(r),
            }
            entry["is_active"] = is_active(entry)
            results.append(entry)
        except Exception as e:
            logger.warning("Open Canada normalize error: %s", e)
    return results


def _map_sam_status(record: dict) -> str:
    active = record.get("active")
    if active == "Yes" or active is True:
        return "active"
    if active == "No" or active is False:
        return "closed"
    archive_type = (record.get("archiveType") or "").lower()
    if archive_type in ("cancelled",):
        return "cancelled"
    return "unknown"


def normalize_sam_gov(records: list[dict]) -> list[dict]:
    results = []
    for r in records:
        try:
            entry = {
                "id": _make_id("sam_gov", r.get("noticeId", r.get("solicitationNumber", ""))),
                "title": _safe_str(r.get("title")) or "Untitled",
                "description": _safe_str(r.get("description")) or "",
                "value": None,
                "currency": "USD",
                "awarded_date": None,
                "close_date": _safe_str(r.get("responseDeadLine")),
                "vendor": None,
                "department": _safe_str(r.get("fullParentPathName") or r.get("organizationName")) or "Unknown",
                "country": "US",
                "source": "sam_gov",
                "url": _safe_str(r.get("uiLink")),
                "status": _map_sam_status(r),
            }
            entry["is_active"] = is_active(entry)
            results.append(entry)
        except Exception as e:
            logger.warning("SAM.gov normalize error: %s", e)
    return results


def normalize_usa_spending(records: list[dict]) -> list[dict]:
    results = []
    for r in records:
        try:
            # USASpending is a spending database — contracts here are awarded
            entry = {
                "id": _make_id("usa_spending", r.get("generated_internal_id", r.get("Award ID", ""))),
                "title": _safe_str(r.get("Description")) or "Untitled",
                "description": "",
                "value": _safe_float(r.get("Award Amount")),
                "currency": "USD",
                "awarded_date": _safe_str(r.get("Award Date")),
                "close_date": _safe_str(r.get("End Date") or r.get("period_of_performance_current_end_date")),
                "vendor": _safe_str(r.get("Recipient Name")),
                "department": _safe_str(r.get("Awarding Agency")) or "Unknown",
                "country": "US",
                "source": "usa_spending",
                "url": f"https://www.usaspending.gov/award/{r['generated_internal_id']}" if r.get("generated_internal_id") else None,
                "status": "awarded",
            }
            entry["is_active"] = is_active(entry)
            results.append(entry)
        except Exception as e:
            logger.warning("USASpending normalize error: %s", e)
    return results
