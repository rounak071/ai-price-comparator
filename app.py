
import os
import uuid

from flask import Flask, render_template, request
from werkzeug.utils import secure_filename

from product_matcher import identify_product
from price_comparator import compare_prices
from visual_search import find_similar_products

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join("static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/identify", methods=["POST"])
def identify():
    image = request.files.get("product_image")

    if not image or not image.filename:
        return "Please select an image.", 400

    if not allowed_file(image.filename):
        return "Only JPG, JPEG and PNG images are allowed.", 400

    safe_name = secure_filename(image.filename)
    extension = safe_name.rsplit(".", 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{extension}"

    save_path = os.path.join(UPLOAD_FOLDER, filename)
    image.save(save_path)

    image_url = "/static/uploads/" + filename

    try:
        # Keep the existing AI predictions.
        predictions = identify_product(save_path)

        # Compare the uploaded image with the local visual catalog.
        similar_products = find_similar_products(
            save_path, top_k=5
        )

        # Create marketplace search links for each matched product.
        for product in similar_products:
            product["stores"] = compare_prices(product["title"])

        # Fallback search links when the catalog has no matches.
        product_name = (
            predictions[0]["label"] if predictions else ""
        )
        fallback_stores = (
            compare_prices(product_name)
            if not similar_products
            else []
        )

        return render_template(
            "results.html",
            image_url=image_url,
            predictions=predictions,
            similar_products=similar_products,
            fallback_stores=fallback_stores,
            error=None
        )

    except Exception:
        app.logger.exception("Product analysis failed")

        return render_template(
            "results.html",
            image_url=image_url,
            predictions=[],
            similar_products=[],
            fallback_stores=[],
            error=(
                "Product analysis failed. "
                "Please check the VS Code terminal."
            )
        ), 500


@app.errorhandler(413)
def file_too_large(error):
    return "Image is too large. Maximum size is 5 MB.", 413


if __name__ == "__main__":
    app.run(debug=True)
