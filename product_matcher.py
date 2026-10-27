
from transformers import pipeline

_model = None


def get_model():
    global _model

    if _model is None:
        _model = pipeline(
            "image-classification",
            model="google/vit-base-patch16-224"
        )

    return _model


def identify_product(image_path):
    model = get_model()
    predictions = model(image_path, top_k=5)

    results = []

    for prediction in predictions:
        results.append({
            "label": prediction["label"],
            "confidence": round(
                prediction["score"] * 100, 2
            )
        })

    return results
