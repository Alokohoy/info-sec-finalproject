import os

from flask import Flask, jsonify, render_template, request

from scraper import (
    DEFAULT_INDEX,
    DEFAULT_URL,
    bulk_index_movies,
    ensure_index,
    es_client,
    require_es_up,
    scrape_movies_from_wikipedia_list,
    search_movies,
)


app = Flask(__name__)


def _settings():
    return {
        "es": os.getenv("ES_URL", "http://localhost:9200"),
        "index": os.getenv("ES_INDEX", DEFAULT_INDEX),
    }


@app.get("/")
def home():
    s = _settings()
    return render_template(
        "index.html",
        default_url=DEFAULT_URL,
        es_url=s["es"],
        index_name=s["index"],
    )


@app.get("/api/es-info")
def api_es_info():
    s = _settings()
    es = es_client(s["es"])
    require_es_up(es, s["es"])
    info = es.info()
    return jsonify(
        {
            "ok": True,
            "cluster_name": info.get("cluster_name"),
            "version": (info.get("version") or {}).get("number"),
            "tagline": info.get("tagline"),
            "es_url": s["es"],
        }
    )


@app.post("/api/scrape-and-index")
def api_scrape_and_index():
    s = _settings()
    payload = request.get_json(silent=True) or {}
    url = (payload.get("url") or DEFAULT_URL).strip()

    es = es_client(s["es"])
    require_es_up(es, s["es"])
    ensure_index(es, s["index"])

    movies = scrape_movies_from_wikipedia_list(url)
    indexed = bulk_index_movies(es, s["index"], movies)

    return jsonify(
        {
            "indexed": indexed,
            "found": len(movies),
            "index": s["index"],
            "source": url,
        }
    )


@app.get("/api/search")
def api_search():
    s = _settings()
    q = (request.args.get("q") or "").strip()
    size = int(request.args.get("size") or "10")
    size = max(1, min(size, 50))

    if not q:
        return jsonify({"error": "q is required"}), 400

    es = es_client(s["es"])
    require_es_up(es, s["es"])

    results = search_movies(es, s["index"], q, size=size)
    return jsonify({"query": q, "results": results})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5055, debug=True)

