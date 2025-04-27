from flask import Flask, request, jsonify
from scraper import scrape_product

app = Flask(__name__)

@app.route("/scrape", methods=["POST"])
def scrape():
    data = request.get_json(force=True)
    url = data.get("url")
    if not url:
        return jsonify({"error": "Proszę podać pole `url` w JSON-ie"}), 400

    try:
        result = scrape_product(url)
    except Exception as e:
        return jsonify({"error": "Błąd scrapowania", "details": str(e)}), 500

    return jsonify(result), 200

if __name__ == "__main__":
    # w Dockerze Flask będzie dostępny na 0.0.0.0:3000
    app.run(host="0.0.0.0", port=3000)
