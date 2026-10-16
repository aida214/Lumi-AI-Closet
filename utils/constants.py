"""Shared option lists so every page uses the same wording."""

CATEGORIES = ["Top", "Bottom", "Dress", "Outerwear", "Shoes", "Accessory"]
SEASONS = ["Spring", "Summer", "Autumn", "Winter", "All Season"]
STYLES = [
    "Casual", "Formal", "Streetwear", "Coquette", "Old Money",
    "Minimalist", "Y2K", "Sporty", "Vintage",
]
OCCASIONS = ["Everyday", "Campus", "Work", "Evening", "Weekend", "Workout"]

# (slot key, label, wardrobe category)
SLOTS = [
    ("top", "Top", "Top"),
    ("bottom", "Bottom", "Bottom"),
    ("dress", "Dress", "Dress"),
    ("outerwear", "Outerwear", "Outerwear"),
    ("shoes", "Shoes", "Shoes"),
    ("accessory", "Bag or accessory", "Accessory"),
]
SLOT_BY_CATEGORY = {cat: key for key, _label, cat in SLOTS}

STORAGE_BUCKET = "wardrobe"
MAX_UPLOAD_MB = 10
