import json
from typing import Any
from app.firestore_tools import get_itinerary


def validate_and_generate_event_logistics(
    event_vibe: str, duration_days: int = 3, attendee_count: int = 8
) -> str:
    """Validate event schedule pacing/conflicts and generate a structured logistics prep checklist.

    Args:
        event_vibe: The overall theme or vibe of the event (e.g. 'Glamorous Bachelorette', 'Coastal Chic').
        duration_days: Length of the celebration event in days (default 3).
        attendee_count: Total number of attending guests.

    Returns:
        JSON string containing schedule validation alerts and structured logistics checklist items.
    """
    try:
        itinerary_items = get_itinerary()
    except Exception as e:
        itinerary_items = []

    # 1. Schedule Conflict & Pacing Validation
    schedule_alerts = []
    days_covered = set()
    times_seen = set()

    for item in itinerary_items:
        day = item.get("day", "Day 1")
        time = item.get("time", "TBD")
        days_covered.add(day)

        key = f"{day}_{time}"
        if key in times_seen:
            schedule_alerts.append(
                f"Schedule Conflict: Multiple activities scheduled on {day} at {time} ('{item.get('activity')}')"
            )
        else:
            times_seen.add(key)

    if len(itinerary_items) == 0:
        schedule_alerts.append(
            "No itinerary items found in Firestore. Add initial events to validate pacing."
        )

    # 2. Logistics & Prep Checklist Items
    checklist = [
        {
            "category": "Pre-Event Planning & RSVPs",
            "task": f"Confirm dietary restrictions & RSVPs for all {attendee_count} attendees",
            "due": "14 days prior",
            "priority": "High",
        },
        {
            "category": "Transport & Buffers",
            "task": f"Arrange group transport suitable for {attendee_count} guests with 30-min buffer between venues",
            "due": "7 days prior",
            "priority": "High",
        },
        {
            "category": "Aesthetic Decor & Collateral",
            "task": f"Source theme props, welcome bags, and custom decor matching the '{event_vibe}' vibe",
            "due": "5 days prior",
            "priority": "Medium",
        },
    ]

    if attendee_count >= 10:
        checklist.append({
            "category": "Large Group Catering",
            "task": f"Confirm private dining room / table layout and prix-fixe menu for {attendee_count} guests",
            "due": "3 days prior",
            "priority": "High",
        })

    result = {
        "event_vibe": event_vibe,
        "duration_days": duration_days,
        "attendee_count": attendee_count,
        "schedule_status": "valid" if not schedule_alerts else "requires_review",
        "schedule_alerts": schedule_alerts,
        "total_scheduled_activities": len(itinerary_items),
        "logistics_checklist": checklist,
    }

    return json.dumps(result, indent=2)
