# Automated Web Scraper + Elasticsearch (Movies)

This mini-project scrapes a public web page with a list of movies (Wikipedia) and indexes the results into **Elasticsearch**, so you can search them instantly.

## What it does

- Scrapes movie rows from a Wikipedia list page (title, year, optional details)
- Normalizes the data
- Indexes documents into Elasticsearch (bulk)
- Lets you run simple search queries

## Requirements

- Docker + Docker Compose
- Python 3.10+

## Quick start

### 1) Start Elasticsearch

```bash
cd AutomatedWebScraperElasticsearch
docker compose up -d
```

Elasticsearch will be available at `http://localhost:9200`.

### 2) Create venv + install deps

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3) Scrape + index

Scrape a Wikipedia page (default is a “List of films …” page) and index into `movies`:

```bash
python scraper.py scrape-and-index
```

Or specify a different URL:

```bash
python scraper.py scrape-and-index \
  --url "https://en.wikipedia.org/wiki/List_of_American_films_of_2024"
```

### 4) Search

```bash
python scraper.py search --q "Dune"
python scraper.py search --q "comedy"
```

## Useful Elasticsearch checks

```bash
curl -s http://localhost:9200 | jq .
curl -s "http://localhost:9200/movies/_count?pretty"
curl -s "http://localhost:9200/movies/_search?q=title:Dune&pretty"
```

## Notes

- Wikipedia markup changes sometimes; the scraper is written to be reasonably tolerant, but you can point it at any similar “list of films” page.
- This is intended as a course/demo project (not a production crawler).

