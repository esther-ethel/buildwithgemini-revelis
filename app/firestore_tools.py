import logging
from typing import Any
from google.cloud import firestore

logger = logging.getLogger(__name__)

# HARDCODED PROJECT ID - DO NOT USE google.auth.default() OR GOOGLE_CLOUD_PROJECT
# On Agent Engine / Platform runtime, GOOGLE_CLOUD_PROJECT evaluates to project NUMBER,
# which causes 404 NOT_FOUND on Firestore.
PROJECT_ID = "qwiklabs-gcp-02-1a0a1ffea9f5"


def get_firestore_client() -> firestore.Client:
    return firestore.Client(project=PROJECT_ID)


def get_itinerary() -> list[dict[str, Any]]:
    """Retrieve all event itinerary items from Firestore.

    Returns:
        List of itinerary entries, each containing day, time, activity, vibe, and dress_code.
    """
    db = get_firestore_client()
    docs = db.collection("itineraries").stream()
    result = []
    for doc in docs:
        item = doc.to_dict()
        item["id"] = doc.id
        result.append(item)
    return result


def add_itinerary_item(
    day: str, time: str, activity: str, vibe: str, dress_code: str
) -> str:
    """Add a new activity/item to the event itinerary in Firestore.

    Args:
        day: Day of the event (e.g. 'Day 1 (Friday)').
        time: Time of the activity (e.g. '19:00').
        activity: Description of the event/activity.
        vibe: Atmosphere or theme vibe (e.g. 'Chic & Relaxed').
        dress_code: Attire guideline (e.g. 'Cocktail Attire').

    Returns:
        Confirmation message with the created document ID.
    """
    db = get_firestore_client()
    doc_ref = db.collection("itineraries").document()
    item = {
        "day": day,
        "time": time,
        "activity": activity,
        "vibe": vibe,
        "dress_code": dress_code,
    }
    doc_ref.set(item)
    return f"Successfully added itinerary item '{activity}' on {day} at {time} with ID {doc_ref.id}."


def get_menu_items() -> list[dict[str, Any]]:
    """Retrieve all food, cocktail, and dessert menu items from Firestore.

    Returns:
        List of menu items, each containing name, type, dietary_flags, description, and image_url.
    """
    db = get_firestore_client()
    docs = db.collection("menu_items").stream()
    result = []
    for doc in docs:
        item = doc.to_dict()
        item["id"] = doc.id
        result.append(item)
    return result


def add_menu_item(
    name: str,
    item_type: str,
    dietary_flags: list[str],
    description: str,
    image_url: str = "",
) -> str:
    """Add a new menu item (cocktail, appetizer, main, dessert) to Firestore.

    Args:
        name: Name of the dish or drink.
        item_type: Type of item ('appetizer', 'main', 'dessert', 'cocktail').
        dietary_flags: List of dietary attributes (e.g. ['vegan', 'nut-free']).
        description: Detailed description of ingredients or preparation.
        image_url: Optional URL to an image asset.

    Returns:
        Confirmation message with the created document ID.
    """
    db = get_firestore_client()
    doc_ref = db.collection("menu_items").document()
    item = {
        "name": name,
        "type": item_type,
        "dietary_flags": dietary_flags,
        "description": description,
        "image_url": image_url,
    }
    doc_ref.set(item)
    return f"Successfully added menu item '{name}' with ID {doc_ref.id}."
