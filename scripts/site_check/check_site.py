"""Post-build checks for marionomics.com (spec: Testing → Build checks). Standard library only.

Usage: python scripts/site_check/check_site.py public redirects.txt --min-indexed 332
"""
from __future__ import annotations

import argparse
import json
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

SITE = "https://marionomics.com"


class _Refs(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs: list[str] = []

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if not value:
                continue
            if name in ("href", "src", "poster"):
                self.refs.append(value)
            elif name == "srcset":
                self.refs += [e.strip().split()[0] for e in value.split(",") if e.strip()]


def _local_refs(html: str):
    parser = _Refs()
    parser.feed(html)
    for ref in parser.refs:
        if ref.startswith(SITE):
            ref = ref[len(SITE):] or "/"
        if ref.startswith("/") and not ref.startswith("//"):
            yield ref


def resolves(public: Path, url: str) -> bool:
    path = unquote(urlsplit(url).path)
    target = public / path.lstrip("/")
    if path.endswith("/"):
        return (target / "index.html").is_file()
    return target.is_file() or (target / "index.html").is_file()


def check_links(public: Path) -> list[str]:
    problems = []
    for page in sorted(public.rglob("*.html")):
        if "pagefind" in page.relative_to(public).parts:
            continue
        for ref in _local_refs(page.read_text(encoding="utf-8", errors="replace")):
            if not resolves(public, ref):
                problems.append(f"{page.relative_to(public).as_posix()}: broken {ref}")
    return problems


def check_redirect_targets(public: Path, redirects: Path) -> list[str]:
    if not redirects.is_file():
        return [f"redirects file missing: {redirects}"]
    problems = []
    for line in redirects.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        old, new = line.split("\t")
        if new.startswith(SITE) and not resolves(public, new[len(SITE):] or "/"):
            problems.append(f"redirect target missing: {old} -> {new}")
    return problems


def check_index(public: Path, minimum: int) -> list[str]:
    entry = public / "pagefind" / "pagefind-entry.json"
    if not entry.is_file():
        return [f"Pagefind index missing: {entry}"]
    languages = json.loads(entry.read_text(encoding="utf-8")).get("languages", {})
    count = sum(lang.get("page_count", 0) for lang in languages.values())
    if count < minimum:
        return [f"Pagefind indexed {count} pages, expected at least {minimum}"]
    return []


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("public", type=Path)
    parser.add_argument("redirects", type=Path)
    parser.add_argument("--min-indexed", type=int, default=332)
    args = parser.parse_args(argv)
    problems = (check_redirect_targets(args.public, args.redirects)
                + check_links(args.public)
                + check_index(args.public, args.min_indexed))
    for problem in problems:
        print(problem)
    print(f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
