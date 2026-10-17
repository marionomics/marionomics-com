"""Load a Ghost export and select the items that migrate (spec: Content scope)."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from scope import KEEP_PAGES


@dataclass(frozen=True)
class Tag:
    slug: str
    name: str


@dataclass
class Item:
    id: str
    slug: str
    kind: str  # "post" or "page"
    title: str
    html: str
    plaintext: str
    published_at: str
    updated_at: str
    custom_excerpt: str | None
    meta_description: str | None
    feature_image: str | None
    feature_image_alt: str | None
    feature_image_caption: str | None
    code_injection: str
    tags: list[Tag] = field(default_factory=list)


def load_export(path: Path) -> dict:
    """Return the `data` object of a Ghost export ({meta, data}) or admin export ({db: [{data}]})."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if "db" in raw:
        return raw["db"][0]["data"]
    return raw["data"]


def _is_public_tag(tag: dict) -> bool:
    return tag.get("visibility", "public") == "public" and not tag["name"].startswith("#")


def _tags_by_post(data: dict) -> dict[str, list[Tag]]:
    tags = {t["id"]: t for t in data.get("tags", [])}
    result: dict[str, list[Tag]] = {}
    for link in sorted(data.get("posts_tags", []), key=lambda pt: pt.get("sort_order", 0)):
        tag = tags.get(link["tag_id"])
        if tag and _is_public_tag(tag):
            result.setdefault(link["post_id"], []).append(Tag(tag["slug"], tag["name"]))
    return result


def _kind(post: dict) -> str | None:
    if post["status"] != "published":
        return None
    if post["type"] == "post":
        return "post"
    if post["type"] == "page" and post["slug"] in KEEP_PAGES:
        return "page"
    return None


def select_items(data: dict) -> list[Item]:
    meta = {m["post_id"]: m for m in data.get("posts_meta", [])}
    tags = _tags_by_post(data)
    items = []
    for post in data["posts"]:
        kind = _kind(post)
        if kind is None:
            continue
        m = meta.get(post["id"], {})
        items.append(Item(
            id=post["id"],
            slug=post["slug"],
            kind=kind,
            title=post["title"],
            html=post.get("html") or "",
            plaintext=post.get("plaintext") or "",
            published_at=post["published_at"],
            updated_at=post["updated_at"],
            custom_excerpt=post.get("custom_excerpt") or None,
            meta_description=m.get("meta_description") or post.get("meta_description") or None,
            feature_image=post.get("feature_image") or None,
            feature_image_alt=m.get("feature_image_alt") or post.get("feature_image_alt") or None,
            feature_image_caption=m.get("feature_image_caption") or post.get("feature_image_caption") or None,
            code_injection=(post.get("codeinjection_head") or "") + (post.get("codeinjection_foot") or ""),
            tags=tags.get(post["id"], []) if kind == "post" else [],
        ))
    items.sort(key=lambda i: i.published_at, reverse=True)
    return items


def used_tags(items: list[Item]) -> list[Tag]:
    seen: dict[str, Tag] = {}
    for item in items:
        for tag in item.tags:
            seen.setdefault(tag.slug, tag)
    return sorted(seen.values(), key=lambda t: t.slug)
