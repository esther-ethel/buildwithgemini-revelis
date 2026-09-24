import logging
from google.cloud import firestore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# HARDCODED PROJECT ID - DO NOT USE google.auth.default() OR GOOGLE_CLOUD_PROJECT
# On Agent Engine / Platform runtime, GOOGLE_CLOUD_PROJECT evaluates to project NUMBER,
# which causes 404 NOT_FOUND on Firestore.
PROJECT_ID = "qwiklabs-gcp-02-1a0a1ffea9f5"

def seed_firestore():
    logger.info(f"Connecting to Firestore with explicit project ID: {PROJECT_ID}")
    db = firestore.Client(project=PROJECT_ID)

    # Sample Itineraries Data
    itineraries = [
        {
            "day": "Day 1 (Friday)",
            "time": "19:00",
            "activity": "Sunset Champagne & Hors d'Oeuvres Welcome Reception",
            "vibe": "Chic & Relaxed",
            "dress_code": "Cocktail Attire",
        },
        {
            "day": "Day 2 (Saturday)",
            "time": "10:30",
            "activity": "Private Yacht Charter & Coastal Brunch",
            "vibe": "Glamorous & Festive",
            "dress_code": "Nautical White / Swimwear",
        },
        {
            "day": "Day 2 (Saturday)",
            "time": "20:00",
            "activity": "Multi-Course Tasting Menu at Chef's Table",
            "vibe": "Sophisticated & Elegant",
            "dress_code": "Black Tie Optional",
        },
        {
            "day": "Day 3 (Sunday)",
            "time": "11:00",
            "activity": "Farewell Detox Spa & Mimosa Brunch",
            "vibe": "Rejuvenating & Cozy",
            "dress_code": "Lounge Chic",
        },
    ]

    logger.info("Seeding 'itineraries' collection...")
    for item in itineraries:
        doc_ref = db.collection("itineraries").document()
        doc_ref.set(item)
        logger.info(f"Added itinerary: {item['activity']} ({doc_ref.id})")

    # Sample Menu Items Data
    menu_items = [
        {
            "name": "Velvet Rose & Champagne Tiered Cake",
            "type": "dessert",
            "dietary_flags": ["vegetarian", "nut-free"],
            "description": "Custom 3-tier elderflower cake with champagne reduction and edible rose gold leaf.",
            "image_url": "",
        },
        {
            "name": "Smoked Sea Salt & Hibiscus Mezcalita",
            "type": "cocktail",
            "dietary_flags": ["vegan", "gluten-free"],
            "description": "Craft cocktail with artisanal mezcal, lime juice, hibiscus syrup, and smoked lava salt rim.",
            "image_url": "",
        },
        {
            "name": "Truffle Ricotta & Wild Mushroom Crostini",
            "type": "appetizer",
            "dietary_flags": ["vegetarian"],
            "description": "Crispy sourdough crostini topped with whipped truffle ricotta, sautéed chanterelles, and thyme.",
            "image_url": "",
        },
        {
            "name": "Seared Wagyu Beef Sliders with Truffle Aioli",
            "type": "main",
            "dietary_flags": ["dairy-free-option"],
            "description": "A5 Wagyu beef sliders served on brioche buns with black truffle aioli and caramelized shallots.",
            "image_url": "",
        },
    ]

    logger.info("Seeding 'menu_items' collection...")
    for item in menu_items:
        doc_ref = db.collection("menu_items").document()
        doc_ref.set(item)
        logger.info(f"Added menu item: {item['name']} ({doc_ref.id})")

    logger.info("Firestore seeding completed successfully!")

if __name__ == "__main__":
    seed_firestore()
