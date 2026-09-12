from typing import Dict, Any, List, Optional

def filter_user(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict):
        return data
    fields = ["id", "name", "first_name", "last_name", "email", "emails", "is_public", "image_id"]
    return {k: data[k] for k in fields if k in data}

def filter_organization(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict):
        return data
    fields = ["id", "name", "vertical", "role"]
    return {k: data[k] for k in fields if k in data}

def filter_venue(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict):
        return data
    fields = ["id", "name", "address", "capacity", "latitude", "longitude", "resource_uri"]
    res = {k: data[k] for k in fields if k in data}
    if "address" in res and isinstance(res["address"], dict):
        addr = res["address"]
        res["address"] = {
            k: addr[k] for k in ["address_1", "address_2", "city", "region", "postal_code", "country", "localized_address_display"]
            if k in addr
        }
    return res

def filter_event(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict):
        return data
    res = {
        "id": data.get("id"),
        "name": data.get("name", {}).get("text") if isinstance(data.get("name"), dict) else data.get("name"),
        "summary": data.get("summary"),
        "status": data.get("status"),
        "start": data.get("start", {}).get("utc") if isinstance(data.get("start"), dict) else data.get("start"),
        "end": data.get("end", {}).get("utc") if isinstance(data.get("end"), dict) else data.get("end"),
        "timezone": data.get("start", {}).get("timezone") if isinstance(data.get("start"), dict) else None,
        "currency": data.get("currency"),
        "online_event": data.get("online_event"),
        "organization_id": data.get("organization_id"),
        "venue_id": data.get("venue_id"),
        "capacity": data.get("capacity"),
        "url": data.get("url")
    }
    return {k: v for k, v in res.items() if v is not None}

def filter_ticket_class(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict):
        return data
    cost = data.get("cost")
    cost_display = cost.get("display") if isinstance(cost, dict) else str(cost) if cost else None
    return {
        "id": data.get("id"),
        "name": data.get("name"),
        "description": data.get("description"),
        "free": data.get("free"),
        "cost": cost_display,
        "quantity_total": data.get("quantity_total"),
        "quantity_sold": data.get("quantity_sold"),
        "on_sale_status": data.get("on_sale_status"),
        "sales_start": data.get("sales_start"),
        "sales_end": data.get("sales_end"),
    }

def filter_attendee(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict):
        return data
    profile = data.get("profile") or {}
    barcodes = [b.get("barcode") for b in data.get("barcodes", []) if isinstance(b, dict) and b.get("barcode")]
    answers = [
        {"question": a.get("question"), "answer": a.get("answer")}
        for a in data.get("answers", []) if isinstance(a, dict)
    ]
    return {
        "id": data.get("id"),
        "event_id": data.get("event_id"),
        "order_id": data.get("order_id"),
        "ticket_class_id": data.get("ticket_class_id"),
        "ticket_class_name": data.get("ticket_class_name"),
        "status": data.get("status"),
        "checked_in": data.get("checked_in"),
        "name": profile.get("name"),
        "email": profile.get("email"),
        "job_title": profile.get("job_title"),
        "company": profile.get("company"),
        "barcodes": barcodes,
        "answers": answers,
        "created": data.get("created")
    }

def filter_order(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict):
        return data
    costs = data.get("costs") or {}
    gross = costs.get("gross", {}).get("display") if isinstance(costs.get("gross"), dict) else None
    return {
        "id": data.get("id"),
        "event_id": data.get("event_id"),
        "name": data.get("name"),
        "first_name": data.get("first_name"),
        "last_name": data.get("last_name"),
        "email": data.get("email"),
        "status": data.get("status"),
        "gross": gross,
        "created": data.get("created"),
        "changed": data.get("changed")
    }

def filter_discount(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict):
        return data
    return {
        "id": data.get("id"),
        "code": data.get("code"),
        "type": data.get("type"),
        "amount_off": data.get("amount_off"),
        "percent_off": data.get("percent_off"),
        "quantity_available": data.get("quantity_available"),
        "quantity_sold": data.get("quantity_sold"),
        "start_date": data.get("start_date"),
        "end_date": data.get("end_date"),
        "event_id": data.get("event_id")
    }

def filter_webhook(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict):
        return data
    return {
        "id": data.get("id"),
        "endpoint_url": data.get("endpoint_url"),
        "actions": data.get("actions"),
        "event_id": data.get("event_id"),
        "user_id": data.get("user_id")
    }

def filter_category(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict):
        return data
    return {
        "id": data.get("id"),
        "name": data.get("name"),
        "name_localized": data.get("name_localized"),
        "short_name": data.get("short_name"),
        "subcategories": [
            {"id": s.get("id"), "name": s.get("name")}
            for s in data.get("subcategories", []) if isinstance(s, dict)
        ] if "subcategories" in data else None
    }

def filter_format(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict):
        return data
    return {
        "id": data.get("id"),
        "name": data.get("name"),
        "short_name": data.get("short_name")
    }

def filter_question(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict):
        return data
    question_text = data.get("question", {}).get("text") if isinstance(data.get("question"), dict) else data.get("question")
    return {
        "id": data.get("id"),
        "question": question_text,
        "type": data.get("type"),
        "required": data.get("required"),
        "ticket_classes": data.get("ticket_classes"),
        "choices": [
            c.get("answer", {}).get("text") if isinstance(c.get("answer"), dict) else c.get("answer")
            for c in data.get("choices", []) if isinstance(c, dict)
        ] if "choices" in data else None
    }

def clean_paginated_response(resp: Dict[str, Any], items_key: str, item_filter_func) -> Dict[str, Any]:
    if resp.get("error"):
        return resp
    raw_items = resp.get(items_key, [])
    filtered_items = [item_filter_func(it) for it in raw_items] if isinstance(raw_items, list) else raw_items
    result = {
        items_key: filtered_items
    }
    if "pagination" in resp and isinstance(resp["pagination"], dict):
        p = resp["pagination"]
        result["pagination"] = {
            "has_more_items": p.get("has_more_items", False),
            "continuation": p.get("continuation"),
            "object_count": p.get("object_count"),
            "page_count": p.get("page_count"),
            "page_number": p.get("page_number")
        }
    return result
