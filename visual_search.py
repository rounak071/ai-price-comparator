
import json
import os

import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CATALOG_FILE = os.path.join(BASE_DIR, "catalog.json")

MODEL_NAME = "openai/clip-vit-base-patch32"

_model = None
_processor = None


def get_clip_model():
    global _model, _processor

    if _model is None:
        _processor = CLIPProcessor.from_pretrained(MODEL_NAME)
        _model = CLIPModel.from_pretrained(MODEL_NAME)
        _model.eval()

    return _model, _processor


def find_similar_products(image_path, top_k=5):
    if not os.path.isfile(CATALOG_FILE):
        return []

    try:
        with open(CATALOG_FILE, "r", encoding="utf-8") as file:
            catalog = json.load(file)
    except (json.JSONDecodeError, OSError):
        return []

    if not isinstance(catalog, list) or not catalog:
        return []

    valid_products = []
    catalog_images = []

    for product in catalog:
        if not isinstance(product, dict):
            continue

        title = product.get("title", "").strip()
        relative_path = product.get("image", "")

        if not title or not relative_path:
            continue

        product_image_path = os.path.join(
            BASE_DIR, relative_path.replace("/", os.sep)
        )

        if not os.path.isfile(product_image_path):
            continue

        try:
            with Image.open(product_image_path) as image:
                catalog_images.append(image.convert("RGB").copy())
                valid_products.append(product)
        except (OSError, ValueError):
            continue

    if not valid_products:
        return []

    try:
        with Image.open(image_path) as image:
            query_image = image.convert("RGB").copy()
    except (OSError, ValueError):
        return []

    model, processor = get_clip_model()

    inputs = processor(
        images=[query_image] + catalog_images,
        return_tensors="pt",
        padding=True
    )

    with torch.no_grad():
        features = model.get_image_features(**inputs)

        # Normalize vectors before calculating similarity.
        features = features / features.norm(
            dim=-1, keepdim=True
        ).clamp(min=1e-12)

        query_features = features[0]
        catalog_features = features[1:]

        scores = catalog_features @ query_features

    ranked_indices = torch.argsort(
        scores, descending=True
    ).tolist()

    results = []

    for index in ranked_indices[:top_k]:
        product = valid_products[index]
        similarity = float(scores[index].item())

        results.append({
            "title": product["title"],
            "image_url": "/" + product["image"].replace("\\", "/"),
            "similarity": round(similarity * 100, 1)
        })

    return results
