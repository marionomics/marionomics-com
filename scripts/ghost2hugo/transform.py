"""HTML rewrite rules for Ghost post bodies (spec: HTML transform rules)."""
from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlsplit

from bs4 import BeautifulSoup, Comment, NavigableString

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
        # Ghost matched slugs case-insensitively; anything after a known slug is pasted junk.
        first = segments[0].lower()
        if first in known_slugs:
            a["href"] = f"/{first}/{fragment}"
        elif len(segments) == 2 and first == "tag" and segments[1].lower() in known_tags:
            a["href"] = f"/tag/{segments[1].lower()}/"
        else:
            report.add(slug, "link_rewritten", href)
            a["href"] = "/"


def replace_membership_cards(soup) -> None:
    for card in soup.select(".kg-signup-card, .kg-product-card"):
        card.replace_with(parse(NOTE_HTML))


# --- Inline math (spec rule 6) ---------------------------------------------------------------

SKIP_TEXT_PARENTS = {"pre", "code", "script", "style"}
LATEXY = re.compile(r"[\\_^{}=+]|^[A-Za-z]$|^[^\s\d]\S{0,19}$")
NUMBER = re.compile(r"^\d+(?:\.\d+)?$")  # $100$: a closing $ glued to digits is never a price
INLINE_MATH = re.compile(r"(?<![$\\])\$(?!\$)([^$\n]{1,200}?)(?<![\\\s])\$(?!\$)")
DISPLAY_MATH = re.compile(r"\$\$.*?\$\$", re.S)


def _text_nodes(soup):
    for node in soup.find_all(string=True):
        if isinstance(node, Comment):
            continue
        if any(parent.name in SKIP_TEXT_PARENTS for parent in node.parents):
            continue
        yield node


def _convert_inline(chunk: str, slug: str, report: Report) -> str:
    def sub(match):
        body = match.group(1)
        if NUMBER.match(body):
            return r"\(" + body + r"\)"
        if body[0].isspace() or body[0].isdigit() or not LATEXY.search(body):
            report.add(slug, "math_left_as_text", match.group(0))
            return match.group(0)
        return r"\(" + body + r"\)"

    return INLINE_MATH.sub(sub, chunk)


def _convert_text(text: str, slug: str, report: Report) -> str:
    out, pos = [], 0
    for block in DISPLAY_MATH.finditer(text):
        out.append(_convert_inline(text[pos:block.start()], slug, report))
        out.append(block.group(0))
        pos = block.end()
    out.append(_convert_inline(text[pos:], slug, report))
    return "".join(out)


def convert_inline_math(soup, slug: str, report: Report) -> None:
    for node in list(_text_nodes(soup)):
        if "$" not in node:
            continue
        new = _convert_text(str(node), slug, report)
        if new != str(node):
            node.replace_with(NavigableString(new))


# --- Code blocks --------------------------------------------------------------------------------

PRISM_LANGS = {"python", "r", "bash", "latex", "markup", "jsx", "markdown", "json"}
LANG_ALIASES = {"html": "markup", "xml": "markup", "shell": "bash", "sh": "bash",
                "terminal": "bash", "tex": "latex", "py": "python"}


def normalize_code_languages(soup) -> None:
    for el in soup.find_all(["pre", "code"], class_=True):
        classes = []
        for cls in el["class"]:
            if cls.startswith("language-"):
                lang = cls[len("language-"):].lower()
                lang = LANG_ALIASES.get(lang, lang)
                cls = f"language-{lang}" if lang in PRISM_LANGS else "language-none"
            classes.append(cls)
        el["class"] = classes


# --- Scripts, injections, unknown cards ---------------------------------------------------------

KNOWN_INJECTION = re.compile(r"katex|prism", re.I)
KNOWN_CARDS = {
    "image", "gallery", "callout", "button", "embed", "bookmark", "file", "product", "signup",
    "video", "audio", "code", "toggle", "header", "html", "markdown", "divider", "email",
    "email-cta", "cta", "paywall", "nft",
}


def handle_scripts(soup, slug: str, report: Report) -> None:
    for script in soup.find_all("script"):
        src = script.get("src") or ""
        if "platform.twitter.com/widgets.js" in src:
            script.decompose()
        else:
            report.add(slug, "inline_script", src or (script.string or "")[:80])


def check_code_injection(code: str, slug: str, report: Report) -> None:
    if not code.strip():
        return
    soup = parse(code)
    for el in soup.find_all(["script", "link", "style"]):
        ref = el.get("src") or el.get("href") or ""
        if KNOWN_INJECTION.search(ref) or "renderMathInElement" in (el.string or ""):
            el.decompose()
    for comment in soup.find_all(string=lambda s: isinstance(s, Comment)):
        comment.extract()
    rest = str(soup).strip()
    if rest:
        report.add(slug, "code_injection", rest[:120])


def report_unknown_cards(soup, slug: str, report: Report) -> None:
    for el in soup.find_all(class_=True):
        for cls in el["class"]:
            match = re.fullmatch(r"kg-([a-z-]+)-card", cls)
            if match and match.group(1) not in KNOWN_CARDS:
                report.add(slug, "unknown_card", cls)


def detect_flags(soup) -> dict:
    text = "".join(str(node) for node in _text_nodes(soup))
    math = "$$" in text or r"\(" in text or r"\[" in text
    twitter = bool(soup.select("blockquote.twitter-tweet"))
    return {"math": math, "twitter": twitter}


# --- Whole item ---------------------------------------------------------------------------------


@dataclass
class Transformed:
    html: str
    math: bool
    twitter: bool
    feature_image: str | None


def _feature_image(item, store, report: Report) -> str | None:
    if not item.feature_image:
        return None
    url = strip_origin(item.feature_image)
    if url.startswith("/content/"):
        if store.copy(url):
            return url
        report.add(item.slug, "feature_image_missing", item.feature_image)
        return None
    if url.startswith(("http://", "https://")):
        return url
    report.add(item.slug, "feature_image_missing", item.feature_image)
    return None


def transform_item(item, known_slugs: set[str], known_tags: set[str], store, report: Report) -> Transformed:
    from assets import process_assets  # local import keeps transform importable without assets

    soup = parse(item.html)
    normalize_urls(soup)
    rewrite_portal_links(soup)
    rewrite_internal_links(soup, item.slug, known_slugs, known_tags, report)
    replace_membership_cards(soup)
    process_assets(soup, store, item.slug, report)
    normalize_code_languages(soup)
    handle_scripts(soup, item.slug, report)
    report_unknown_cards(soup, item.slug, report)
    convert_inline_math(soup, item.slug, report)
    check_code_injection(item.code_injection, item.slug, report)
    flags = detect_flags(soup)
    return Transformed(str(soup), flags["math"], flags["twitter"], _feature_image(item, store, report))
