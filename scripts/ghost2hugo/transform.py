"""HTML rewrite rules for Ghost post bodies (spec: HTML transform rules)."""
from __future__ import annotations

import re
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

from report import Report
from scope import SUBSTACK_SUBSCRIBE_URL, SUBSTACK_URL

GHOST_ORIGIN = re.compile(r"^(?:__GHOST_URL__|https?://(?:www\.)?marionomics\.com)(?=/|$|[?#])")
URL_ATTRS = ("href", "src", "poster")
NOTE_HTML = (
    f'<p class="substack-note"><a href="{SUBSTACK_URL}">Escribo cada semana en Substack →</a></p>'
)


def parse(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def strip_origin(url: str) -> str:
    """Turn Ghost-origin URLs into root-relative paths; leave everything else alone."""
    url = url.strip()
    stripped = GHOST_ORIGIN.sub("", url, count=1)
    if stripped == url:
        return url
    return stripped if stripped.startswith("/") else "/" + stripped


def normalize_urls(soup) -> None:
    for el in soup.find_all(True):
        for attr in URL_ATTRS:
            if el.has_attr(attr):
                el[attr] = strip_origin(el[attr])
        if el.has_attr("srcset"):
            entries = []
            for entry in el["srcset"].split(","):
                bits = entry.strip().split()
                if bits:
                    bits[0] = strip_origin(bits[0])
                    entries.append(" ".join(bits))
            el["srcset"] = ", ".join(entries)


def rewrite_portal_links(soup) -> None:
    for a in soup.find_all(href=True):
        if "#/portal/" in a["href"]:
            a["href"] = SUBSTACK_SUBSCRIBE_URL


def rewrite_internal_links(soup, slug: str, known_slugs: set[str], known_tags: set[str],
                           report: Report) -> None:
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not href.startswith("/") or href.startswith("//"):
            continue
        parts = urlsplit(href)
        segments = [s for s in parts.path.split("/") if s]
        if not segments or segments[0] in ("content", "tools"):
            continue
        fragment = f"#{parts.fragment}" if parts.fragment else ""
        if len(segments) == 1 and segments[0] in known_slugs:
            a["href"] = f"/{segments[0]}/{fragment}"
        elif len(segments) == 2 and segments[0] == "tag" and segments[1] in known_tags:
            a["href"] = f"/tag/{segments[1]}/"
        else:
            report.add(slug, "link_rewritten", href)
            a["href"] = "/"


def replace_membership_cards(soup) -> None:
    for card in soup.select(".kg-signup-card, .kg-product-card"):
        card.replace_with(parse(NOTE_HTML))
