"""Copy Ghost assets that exist in the backup; remove references to those that don't (spec: Assets)."""
from __future__ import annotations

import re
import shutil
from pathlib import Path
from urllib.parse import unquote, urlsplit

from report import Report

ASSET_PATH = re.compile(r"^/content/(images|files|media)/(.+)$")
SIZE_PREFIX = re.compile(r"^size/w\d+(?:h\d+)?/(?:format/\w+/)?")
CARD_CLASSES = ("kg-image-card", "kg-file-card", "kg-video-card", "kg-audio-card")


class AssetStore:
    def __init__(self, content_root: Path, static_root: Path):
        self.content_root = Path(content_root)
        self.static_root = Path(static_root)
        self.copied: dict[str, int] = {}

    @staticmethod
    def _decoded(url_path: str) -> str:
        return unquote(urlsplit(url_path).path)

    def resolve(self, url_path: str) -> Path | None:
        match = ASSET_PATH.match(self._decoded(url_path))
        if not match:
            return None
        kind, rel = match.groups()
        exact = self.content_root / kind / rel
        if exact.is_file():
            return exact
        original = self.content_root / kind / SIZE_PREFIX.sub("", rel)
        return original if original.is_file() else None

    def copy(self, url_path: str) -> bool:
        source = self.resolve(url_path)
        if source is None:
            return False
        rel = self._decoded(url_path).lstrip("/")
        if rel not in self.copied:
            dest = self.static_root / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)
            self.copied[rel] = source.stat().st_size
        return True

    @property
    def bytes_copied(self) -> int:
        return sum(self.copied.values())


def _is_local(url: str) -> bool:
    return url.startswith("/content/")


def _attached(el, soup) -> bool:
    return any(parent is soup for parent in el.parents)


def _is_missing_site_image(el) -> bool:
    """A root-relative <img> outside /content/ (e.g. Ghost's /favicon.png) has no file on the blog."""
    src = el.get("src") or ""
    return el.name == "img" and src.startswith("/") and not src.startswith(("//", "/content/"))


def _removal_target(el):
    """The element to delete when el's asset is missing: its card, gallery tile or figure."""
    if el.find_parent(class_="kg-bookmark-card") is not None:
        return el  # a bookmark still works without its icon or thumbnail
    for ancestor in el.parents:
        if ancestor.name == "[document]":
            break
        classes = ancestor.get("class", [])
        if "kg-gallery-image" in classes or any(c in classes for c in CARD_CLASSES):
            return ancestor
        if ancestor.name == "figure":
            return ancestor
    return el


def _prune_srcsets(soup, store: AssetStore) -> None:
    for el in soup.find_all(srcset=True):
        kept = []
        for entry in el["srcset"].split(","):
            bits = entry.strip().split()
            if bits and (not _is_local(bits[0]) or store.copy(bits[0])):
                kept.append(" ".join(bits))
        if kept:
            el["srcset"] = ", ".join(kept)
        else:
            del el["srcset"]
            if el.has_attr("sizes"):
                del el["sizes"]


def process_assets(soup, store: AssetStore, slug: str, report: Report) -> None:
    _prune_srcsets(soup, store)
    missing = []
    for el in soup.find_all(True):
        for attr in ("src", "href", "poster"):
            url = el.get(attr)
            if url and _is_local(url) and not store.copy(url):
                missing.append((el, url))
        if _is_missing_site_image(el):
            missing.append((el, el["src"]))
    for el, url in missing:
        if not _attached(el, soup):
            continue
        report.add(slug, "asset_removed", url)
        target = _removal_target(el)
        if target is el and el.name == "a":
            el.unwrap()
            continue
        gallery = None
        if "kg-gallery-image" in target.get("class", []):
            gallery = target.find_parent(class_="kg-gallery-card")
        target.decompose()
        if gallery is not None and not gallery.find("img"):
            gallery.decompose()
