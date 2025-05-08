# AI predictor module for tags, etc.
import random

# Placeholder tags for demo purposes
DEFAULT_TAGS = [
    "nature", "portrait", "landscape", "travel", "food", "architecture",
    "wildlife", "street", "black-and-white", "sunset", "mountain",
    "beach", "city", "night", "macro", "sport", "fashion", "event",
    "art", "architecture"
]


def suggest_tags(image_path: str, top_k: int = 10) -> list[str]:
    """
    Stub function for AI-based tag suggestions.
    For now, returns a random sample of DEFAULT_TAGS.
    Replace with real ML model inference.

    :param image_path: Path to the image file
    :param top_k: Number of suggestions to return
    :return: List of suggested tag strings
    """
    # In production, load your ML model here and run inference on image_path
    # Example:
    # embeddings = model.encode_image(image_path)
    # tags = tokenizer.decode_top_k(embeddings, k=top_k)

    # For demo, just random sample
    return random.sample(DEFAULT_TAGS, k=min(top_k, len(DEFAULT_TAGS)))
