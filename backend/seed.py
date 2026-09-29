import requests
from datetime import date

BASE = "http://localhost:8000"

contacts = [
    {"id": "sarah", "name": "Sarah", "company": "ABC Corp"},
    {"id": "rahul", "name": "Rahul", "company": "Internal Manager"},
    {"id": "ananya", "name": "Ananya", "company": "Partner Co"},
]

for c in contacts:
    r = requests.post(f"{BASE}/contacts", json=c)
    print("contact", c["name"], r.status_code)

meetings = [
    {
        "contact_id": "sarah",
        "date": "2026-09-12",
        "notes": "Sarah raised concerns about security compliance. She wants a full audit before rollout. I said I would investigate the audit requirements."
    },
    {
        "contact_id": "sarah",
        "date": "2026-09-19",
        "notes": "Security concerns are resolved. Sarah's priority has shifted to the implementation timeline. I promised to send a roadmap by September 20."
    },
    {
        "contact_id": "sarah",
        "date": "2026-09-29",
        "notes": "Sarah is still waiting for the roadmap. The implementation timeline is the main priority. We should agree on the next milestone and deadline."
    },
    {
        "contact_id": "rahul",
        "date": "2026-09-10",
        "notes": "Weekly 1:1. Rahul is waiting for budget approval. I promised to follow up with finance."
    },
    {
        "contact_id": "rahul",
        "date": "2026-09-17",
        "notes": "Budget approval is still pending. Rahul asked for an update. I said I would check again."
    },
    {
        "contact_id": "rahul",
        "date": "2026-09-24",
        "notes": "Budget approval remains unresolved. Rahul wants a concrete status update before the next 1:1."
    },
    {
        "contact_id": "ananya",
        "date": "2026-09-05",
        "notes": "Ananya said the partnership could move forward within two months if the proposal is accepted."
    },
    {
        "contact_id": "ananya",
        "date": "2026-09-15",
        "notes": "Ananya changed the plan. The partnership is now being postponed to January."
    },
    {
        "contact_id": "ananya",
        "date": "2026-09-28",
        "notes": "January remains the current target. Ananya wants to revisit scope before committing to a date."
    },
]

for m in meetings:
    r = requests.post(f"{BASE}/meetings", json=m)
    print("meeting", m["contact_id"], m["date"], r.status_code, r.text[:150])
