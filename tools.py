"""Three standalone Unit 3 tools; model calls use the starter adapter."""

import json
import re

import config
from generate import generate
from utils.data_loader import load_listings


def _size_tokens(size: str) -> set[str]:
    """Compare size labels without confusing S/US or L/XL."""
    label = re.sub(r"\([^)]*\)", "", size.casefold())
    if "one size" in label:
        return {"one size"}
    label = re.sub(r"\bus\s*", "", label)
    return set(re.findall(r"[a-z]+\d*|\d+(?:\.\d+)?", label))


def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """Return keyword-ranked listings satisfying optional size and budget.

    All words are case-insensitive. Every requested size token must match a
    listing size token; M matches S/M, L never matches XL, and 8 matches US 8
    but not US 8.5. Prices at the ceiling are included. Equal scores retain
    dataset order. Blank descriptions and no matches return an empty list.
    """
    keywords = set(re.findall(r"\w+", description.casefold()))
    if not keywords:
        return []

    requested_size = _size_tokens(size) if size is not None else None
    scored = []
    for listing in load_listings():
        if max_price is not None and listing["price"] > max_price:
            continue
        if requested_size is not None and (
            not requested_size
            or not requested_size.issubset(_size_tokens(listing["size"]))
        ):
            continue
        searchable = " ".join([
            listing["title"], listing["description"], listing["category"],
            *listing["style_tags"], *listing["colors"], listing.get("brand") or "",
        ])
        words = set(re.findall(r"\w+", searchable.casefold()))
        score = len(keywords & words)
        if score:
            scored.append((score, listing))

    scored.sort(key=lambda entry: entry[0], reverse=True)
    return [listing for _, listing in scored[:config.SEARCH_RESULT_LIMIT]]


def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """Return one or two outfits, or general advice for an empty wardrobe."""
    items = wardrobe.get("items", [])
    if items:
        instruction = (
            "Suggest one or two outfits featuring the new item and specific "
            "pieces from the saved wardrobe. Name the wardrobe pieces exactly "
            "so the user can recognize them. Use only the provided wardrobe "
            "pieces as owned items. Explain the color or silhouette pairing."
        )
    else:
        instruction = (
            "The wardrobe is empty. Give one or two general styling ideas for "
            "the new item. Suggested pieces are possibilities, not items the "
            "user owns. Do not claim anything is in their wardrobe."
        )
    prompt = (
        f"{instruction}\nKeep the response concise and return plain text. "
        "Missing brand information is fine; do not invent a brand.\n"
        f"New item: {json.dumps(new_item, ensure_ascii=False)}\n"
        f"Saved wardrobe items: {json.dumps(items, ensure_ascii=False)}"
    )
    response = generate(prompt, system="You are a practical thrift styling assistant.")
    return response.strip() or (
        f"For {new_item['title']}, try simple neutral basics and comfortable "
        "shoes, balancing a loose piece with a more fitted one. These are "
        "general styling ideas; choose pieces you have or would like to find."
    )


def create_fit_card(outfit: str, new_item: dict) -> str:
    """Return a short caption; an empty outfit gets a message without a call."""
    if not outfit.strip():
        return (
            "No outfit suggestion was provided. "
            "Add an outfit before creating a fit card."
        )

    price = f"${new_item['price']:.2f}"
    prompt = (
        "Write a two-to-four sentence social caption someone would actually "
        "post about this thrift find. Return just the caption as one paragraph. "
        "Mention the exact item title, its price, and its platform once each. "
        "Use the supplied price text exactly. Be specific about the outfit's "
        "vibe, with a casual personal voice rather than a product description. "
        "Do not invent a brand or claim the user bought or owns the new item.\n"
        f"Item: {json.dumps(new_item, ensure_ascii=False)}\n"
        f"Price text: {price}\nOutfit suggestion: {outfit}"
    )
    response = generate(prompt, system="You write concise, natural thrift outfit captions.")
    return response.strip() or (
        f"Found {new_item['title']} for {price} on {new_item['platform']}. "
        "I'd keep the styling relaxed with balanced proportions for an "
        "easy thrifted look."
    )
