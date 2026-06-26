"""hubspot-crm — Search, upsert, and log activity on HubSpot CRM contacts via the v3 API."""
import json
import os
import sys

import httpx

BASE = "https://api.hubapi.com"
CONTACT_PROPS = ["email", "firstname", "lastname", "company", "jobtitle", "lifecyclestage"]


def _client(token: str) -> httpx.Client:
    return httpx.Client(
        base_url=BASE,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        timeout=30,
    )


def _shape(obj: dict) -> dict:
    p = obj.get("properties", {})
    return {
        "id": obj.get("id"),
        "email": p.get("email"),
        "name": " ".join(x for x in [p.get("firstname"), p.get("lastname")] if x) or None,
        "company": p.get("company"),
        "jobtitle": p.get("jobtitle"),
        "lifecyclestage": p.get("lifecyclestage"),
    }


def search_contact(c: httpx.Client, inp: dict) -> dict:
    email = (inp.get("email") or "").strip()
    company = (inp.get("company") or "").strip()
    limit = int(inp.get("limit") or 10)
    if email:
        flt = {"propertyName": "email", "operator": "EQ", "value": email}
    elif company:
        flt = {"propertyName": "company", "operator": "CONTAINS_TOKEN", "value": company}
    else:
        raise ValueError("search_contact requires email or company")
    body = {
        "filterGroups": [{"filters": [flt]}],
        "properties": CONTACT_PROPS,
        "limit": max(1, min(limit, 100)),
    }
    r = c.post("/crm/v3/objects/contacts/search", json=body)
    r.raise_for_status()
    results = [_shape(o) for o in r.json().get("results", [])]
    return {"ok": True, "count": len(results), "contacts": results}


def _find_id_by_email(c: httpx.Client, email: str):
    body = {
        "filterGroups": [{"filters": [{"propertyName": "email", "operator": "EQ", "value": email}]}],
        "properties": ["email"],
        "limit": 1,
    }
    r = c.post("/crm/v3/objects/contacts/search", json=body)
    r.raise_for_status()
    results = r.json().get("results", [])
    return results[0]["id"] if results else None


def upsert_contact(c: httpx.Client, inp: dict) -> dict:
    email = (inp.get("email") or "").strip()
    if not email:
        raise ValueError("upsert_contact requires email")
    props = {"email": email}
    for k in ("firstname", "lastname", "company", "jobtitle", "lifecyclestage"):
        if inp.get(k):
            props[k] = inp[k]
    extra = inp.get("properties") or {}
    if isinstance(extra, dict):
        props.update({k: v for k, v in extra.items() if v is not None})

    existing_id = _find_id_by_email(c, email)
    if existing_id:
        r = c.patch(f"/crm/v3/objects/contacts/{existing_id}", json={"properties": props})
        r.raise_for_status()
        return {"ok": True, "action": "updated", "id": existing_id, "contact": _shape(r.json())}
    r = c.post("/crm/v3/objects/contacts", json={"properties": props})
    r.raise_for_status()
    obj = r.json()
    return {"ok": True, "action": "created", "id": obj.get("id"), "contact": _shape(obj)}


def log_engagement(c: httpx.Client, inp: dict) -> dict:
    email = (inp.get("email") or "").strip()
    note = (inp.get("note") or "").strip()
    if not email:
        raise ValueError("log_engagement requires email")
    if not note:
        raise ValueError("log_engagement requires note")
    contact_id = _find_id_by_email(c, email)
    if not contact_id:
        raise ValueError(f"no contact found for email {email}; upsert_contact first")
    # Create the note with a contact association in one call (assoc type 202 = note→contact).
    body = {
        "properties": {"hs_note_body": note, "hs_timestamp": _now_ms(c)},
        "associations": [
            {
                "to": {"id": contact_id},
                "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 202}],
            }
        ],
    }
    r = c.post("/crm/v3/objects/notes", json=body)
    r.raise_for_status()
    return {"ok": True, "note_id": r.json().get("id"), "contact_id": contact_id}


def _now_ms(c: httpx.Client) -> int:
    # HubSpot accepts an ISO-8601 string too, but it also accepts epoch millis.
    # Pull server time off a response Date header to avoid relying on sandbox clock libs.
    r = c.get("/crm/v3/objects/contacts", params={"limit": 1})
    date_hdr = r.headers.get("Date")
    if date_hdr:
        from email.utils import parsedate_to_datetime

        return int(parsedate_to_datetime(date_hdr).timestamp() * 1000)
    import time

    return int(time.time() * 1000)


def main() -> int:
    try:
        inp = json.loads(os.environ.get("INPUT_JSON") or "{}")
        token = os.environ.get("HUBSPOT_ACCESS_TOKEN", "").strip()
        if not token:
            print(json.dumps({"error": "HUBSPOT_ACCESS_TOKEN not set. Add it to the .env next to SKILL.md, or rerun `oya agent skills add` and supply it at the prompt."}))
            return 1

        action = inp.get("action")
        handlers = {
            "search_contact": search_contact,
            "upsert_contact": upsert_contact,
            "log_engagement": log_engagement,
        }
        if action not in handlers:
            print(json.dumps({"error": f"unknown action: {action!r}. Use one of {list(handlers)}"}))
            return 1

        with _client(token) as c:
            result = handlers[action](c, inp)
        print(json.dumps(result, default=str))
        return 0
    except httpx.HTTPStatusError as e:
        detail = ""
        try:
            detail = e.response.json().get("message", "")
        except Exception:
            detail = e.response.text[:300]
        print(json.dumps({"error": f"HubSpot {e.response.status_code}: {detail}", "type": "HTTPStatusError"}))
        return 1
    except Exception as e:
        print(json.dumps({"error": str(e), "type": type(e).__name__}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
