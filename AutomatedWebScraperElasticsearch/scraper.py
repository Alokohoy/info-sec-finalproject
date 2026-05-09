import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Optional

import requests
from bs4 import BeautifulSoup
from elasticsearch import Elasticsearch, helpers


DEFAULT_URL = "https://en.wikipedia.org/wiki/List_of_American_films_of_2024"
DEFAULT_INDEX = "movies"


@dataclass(frozen=True)
class Movie:
    title: str
    year: int
    source_url: str
    details_url: Optional[str] = None
    section: Optional[str] = None

    def doc_id(self) -> str:
        h = hashlib.sha256()
        h.update(self.source_url.encode("utf-8"))
        h.update(b"\n")
        h.update(str(self.year).encode("utf-8"))
        h.update(b"\n")
        h.update(self.title.lower().strip().encode("utf-8"))
        return h.hexdigest()[:32]

    def to_doc(self) -> dict:
        return {
            "title": self.title,
            "year": self.year,
            "source_url": self.source_url,
            "details_url": self.details_url,
            "section": self.section,
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        }


def _http_get(url: str, timeout_s: int = 30) -> str:
    headers = {
        "User-Agent": "InfoSecCourseScraper/1.0 (educational project; contact: none)",
        "Accept": "text/html,application/xhtml+xml",
    }
    r = requests.get(url, headers=headers, timeout=timeout_s)
    r.raise_for_status()
    return r.text


def _clean_title(s: str) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    s = s.replace("\u200b", "")
    return s


def scrape_movies_from_wikipedia_list(url: str) -> list[Movie]:
    """
    Scrapes movie titles from a typical Wikipedia "List of ... films of YEAR" page.
    Strategy:
      - Find all sortable wikitable tables
      - Identify a "Title" (or "Film") column
      - Read the first anchor/text in that column per row
    """
    html = _http_get(url)
    soup = BeautifulSoup(html, "html.parser")

    year_match = re.search(r"\b(19\d{2}|20\d{2})\b", url)
    if year_match:
        year = int(year_match.group(1))
    else:
        year = datetime.now().year

    movies: list[Movie] = []

    # Try to carry the nearest section header (e.g., month/quarter headings)
    for table in soup.select("table.wikitable"):
        headers = [th.get_text(" ", strip=True).lower() for th in table.select("tr th")]
        # Wikipedia has many tables; focus on ones likely listing films.
        if not any(h in headers for h in ("title", "film")):
            continue

        # Determine title column index using header row.
        header_row = table.find("tr")
        if not header_row:
            continue
        ths = header_row.find_all(["th", "td"])
        title_idx = None
        for i, th in enumerate(ths):
            label = th.get_text(" ", strip=True).lower()
            if label in ("title", "film"):
                title_idx = i
                break
        if title_idx is None:
            continue

        # Figure section by walking back to previous heading (h2/h3)
        section = None
        prev = table
        for _ in range(30):
            prev = prev.find_previous()
            if not prev:
                break
            if prev.name in ("h2", "h3"):
                section = prev.get_text(" ", strip=True)
                section = section.replace("[edit]", "").strip()
                break

        for tr in table.select("tr")[1:]:
            tds = tr.find_all(["td", "th"])
            if len(tds) <= title_idx:
                continue
            cell = tds[title_idx]

            a = cell.find("a", href=True)
            title = None
            details_url = None
            if a and a.get_text(strip=True):
                title = a.get_text(" ", strip=True)
                details_url = "https://en.wikipedia.org" + a["href"] if a["href"].startswith("/") else a["href"]
            else:
                title = cell.get_text(" ", strip=True)

            title = _clean_title(title)
            if not title:
                continue

            movies.append(
                Movie(
                    title=title,
                    year=year,
                    source_url=url,
                    details_url=details_url,
                    section=section,
                )
            )

    # De-duplicate by doc_id
    uniq: dict[str, Movie] = {m.doc_id(): m for m in movies}
    return list(uniq.values())


def es_client(es_url: str) -> Elasticsearch:
    return Elasticsearch(es_url)


def ensure_index(es: Elasticsearch, index: str) -> None:
    if es.indices.exists(index=index):
        return
    es.indices.create(
        index=index,
        mappings={
            "properties": {
                "title": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                "year": {"type": "integer"},
                "section": {"type": "keyword"},
                "source_url": {"type": "keyword"},
                "details_url": {"type": "keyword"},
                "scraped_at": {"type": "date"},
            }
        },
    )


def bulk_index_movies(es: Elasticsearch, index: str, movies: Iterable[Movie]) -> int:
    actions = (
        {
            "_op_type": "index",
            "_index": index,
            "_id": m.doc_id(),
            "_source": m.to_doc(),
        }
        for m in movies
    )
    ok, _ = helpers.bulk(es, actions, refresh=True)
    return ok


def search_movies(es: Elasticsearch, index: str, q: str, size: int = 10) -> list[dict]:
    resp = es.search(
        index=index,
        size=size,
        query={
            "multi_match": {
                "query": q,
                "fields": ["title^3", "section"],
            }
        },
    )
    hits = resp.get("hits", {}).get("hits", [])
    return [
        {
            "score": h.get("_score"),
            "id": h.get("_id"),
            **(h.get("_source") or {}),
        }
        for h in hits
    ]


def cmd_scrape_and_index(args: argparse.Namespace) -> int:
    es = es_client(args.es)
    ensure_index(es, args.index)

    movies = scrape_movies_from_wikipedia_list(args.url)
    if not movies:
        print("No movies found. Try a different URL.", file=sys.stderr)
        return 2

    count = bulk_index_movies(es, args.index, movies)
    print(json.dumps({"indexed": count, "index": args.index, "source": args.url}, indent=2))
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    es = es_client(args.es)
    results = search_movies(es, args.index, args.q, size=args.size)
    print(json.dumps({"query": args.q, "results": results}, indent=2, ensure_ascii=False))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Scrape movies and index into Elasticsearch.")
    p.add_argument("--es", default="http://localhost:9200", help="Elasticsearch URL")
    p.add_argument("--index", default=DEFAULT_INDEX, help="Elasticsearch index name")

    sub = p.add_subparsers(dest="cmd", required=True)

    s1 = sub.add_parser("scrape-and-index", help="Scrape Wikipedia list page and index results.")
    s1.add_argument("--url", default=DEFAULT_URL, help="Wikipedia list URL to scrape")
    s1.set_defaults(func=cmd_scrape_and_index)

    s2 = sub.add_parser("search", help="Search indexed movies.")
    s2.add_argument("--q", required=True, help="Query string")
    s2.add_argument("--size", type=int, default=10, help="Number of results")
    s2.set_defaults(func=cmd_search)

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

