"""Write Hugo content files, tag term pages, redirects.txt (spec: Front matter, Outputs)."""
from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

from scope import BLOG_URL, DROPPED_PAGE_TARGETS

MEXICO = ZoneInfo("America/Mexico_City")
GENERATED = ("content/posts", "content/pages", "content/tags", "static/content")


def to_mexico(iso: str) -> str:
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(MEXICO).isoformat()


def _description(item) -> str:
    if item.meta_description:
        return item.meta_description
    if item.custom_excerpt:
        return item.custom_excerpt
    text = " ".join(item.plaintext.split())
    return text if len(text) <= 160 else text[:159].rstrip() + "…"


def front_matter(item, t) -> dict:
    fm = {
        "title": item.title,
        "slug": item.slug,
        "date": to_mexico(item.published_at),
        "lastmod": to_mexico(item.updated_at),
    }
    if item.custom_excerpt:
        fm["subtitle"] = item.custom_excerpt
    fm["description"] = _description(item)
    if item.kind == "post":
        fm["tags"] = [tag.slug for tag in item.tags]
    if t.feature_image:
        fm["feature_image"] = t.feature_image
        if item.feature_image_alt:
            fm["feature_image_alt"] = item.feature_image_alt
        if item.feature_image_caption:
            fm["feature_image_caption"] = item.feature_image_caption
    fm["math"] = t.math
    fm["twitter"] = t.twitter
    fm["ghost_id"] = item.id
    return fm


def _yaml(data: dict) -> str:
    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=10_000)


def clean_outputs(out_root: Path) -> None:
    for rel in GENERATED:
        shutil.rmtree(Path(out_root) / rel, ignore_errors=True)


def write_item(out_root: Path, item, t) -> Path:
    folder = "posts" if item.kind == "post" else "pages"
    path = Path(out_root) / "content" / folder / f"{item.slug}.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{_yaml(front_matter(item, t))}---\n{t.html}\n", encoding="utf-8")
    return path


def write_tag_pages(out_root: Path, tags) -> None:
    for tag in tags:
        path = Path(out_root) / "content" / "tags" / tag.slug / "_index.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"---\n{_yaml({'title': tag.name})}---\n", encoding="utf-8")


def redirect_lines(items, tags) -> list[str]:
    lines = [f"/{item.slug}/\t{BLOG_URL}/{item.slug}/" for item in items]
    lines += [f"/tag/{tag.slug}/\t{BLOG_URL}/tag/{tag.slug}/" for tag in tags]
    for slug, target in DROPPED_PAGE_TARGETS.items():
        lines.append(f"/{slug}/\t{BLOG_URL}/" if target == "/" else f"/{slug}/\t{target}")
    return lines


def write_redirects(out_root: Path, items, tags) -> None:
    text = "\n".join(redirect_lines(items, tags)) + "\n"
    (Path(out_root) / "redirects.txt").write_text(text, encoding="utf-8")
