"""Post-build checks for marionomics.com (spec: Testing → Build checks). Standard library only.

Usage: python scripts/site_check/check_site.py public redirects.txt --min-indexed 332 --min-archive 326
"""
from __future__ import annotations

import argparse
import json
import re
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


def _lines(redirects: Path):
    for line in redirects.read_text(encoding="utf-8").splitlines():
        if line.strip():
            yield line.split("\t")


def _page_file(public: Path, path: str) -> Path:
    target = public / unquote(path).lstrip("/")
    return target if target.is_file() else target / "index.html"


def check_redirect_targets(public: Path, redirects: Path) -> list[str]:
    if not redirects.is_file():
        return [f"redirects file missing: {redirects}"]
    problems = []
    for old, new in _lines(redirects):
        if new.startswith(SITE) and not resolves(public, new[len(SITE):] or "/"):
            problems.append(f"redirect target missing: {old} -> {new}")
    return problems


_REFRESH = re.compile(r"http-equiv=[\"']?refresh[\"']?\s+content=[\"']?\d+;\s*url=([^\"'>\s]+)", re.I)


def _refresh_target(html: str) -> str | None:
    match = _REFRESH.search(html)
    return match.group(1) if match else None


def check_old_paths(public: Path, redirects: Path) -> list[str]:
    if not redirects.is_file():
        return [f"redirects file missing: {redirects}"]
    problems = []
    for old, new in _lines(redirects):
        if not resolves(public, old):
            problems.append(f"old path missing: {old}")
        elif new != SITE + old and _refresh_target(
                _page_file(public, old).read_text(encoding="utf-8", errors="replace")) != new:
            problems.append(f"old path not redirecting: {old} -> {new}")
    return problems


_LANDING_RULES = (
    ("landing: missing form", lambda h: len(re.findall(r"class=[\"']?nf-form", h)) >= 2),
    ("landing: missing done section", lambda h: re.search(r"id=[\"']?done[\"'\s>]", h)),
    ("landing: missing archive link", lambda h: re.search(r"href=[\"']?/archivo/", h)),
    ("landing: has blog header", lambda h: not re.search(r"class=[\"']?top[\"'\s>]", h)),
)


def check_landing(public: Path) -> list[str]:
    page = public / "index.html"
    if not page.is_file():
        return ["landing missing"]
    html = page.read_text(encoding="utf-8", errors="replace")
    return [message for message, ok in _LANDING_RULES if not ok(html)]


def check_archive(public: Path, minimum: int) -> list[str]:
    page = public / "archivo" / "index.html"
    if not page.is_file():
        return ["archive missing"]
    count = len(re.findall(r"<li[\s>]", page.read_text(encoding="utf-8", errors="replace")))
    if count < minimum:
        return [f"archive lists {count} posts, expected at least {minimum}"]
    return []


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
    parser.add_argument("--min-archive", type=int, default=326)
    args = parser.parse_args(argv)
    problems = (check_redirect_targets(args.public, args.redirects)
                + check_old_paths(args.public, args.redirects)
                + check_landing(args.public)
                + check_archive(args.public, args.min_archive)
                + check_links(args.public)
                + check_index(args.public, args.min_indexed))
    for problem in problems:
        print(problem)
    print(f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
