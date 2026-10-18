"""Convert a Ghost backup into Hugo content for marionomics.com.

Usage, from the marionomics-com repo root:

    scripts/ghost2hugo/.venv/bin/python scripts/ghost2hugo/ghost2hugo.py \\
        --export ~/Documents/trabajo/coding/marionomics-app/resources/ghost-content/data/<backup>.json \\
        --content ~/Documents/trabajo/coding/marionomics-app/resources/ghost-content \\
        --out .

Rewrites content/posts, content/pages, content/tags, static/content, redirects.txt and report.md.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from assets import AssetStore
from emit import clean_outputs, write_item, write_redirects, write_tag_pages
from extract import load_export, select_items, used_tags
from report import Report
from transform import transform_item


def run(export: Path, content: Path, out: Path) -> tuple[Report, dict[str, str]]:
    out = Path(out)
    if not (out / "hugo.toml").is_file():
        raise SystemExit(f"{out} is not the Hugo repo root (no hugo.toml)")
    items = select_items(load_export(Path(export)))
    tags = used_tags(items)
    clean_outputs(out)
    store = AssetStore(Path(content), out / "static")
    report = Report()
    known_slugs = {item.slug for item in items}
    known_tags = {tag.slug for tag in tags}
    for item in items:
        write_item(out, item, transform_item(item, known_slugs, known_tags, store, report))
    write_tag_pages(out, tags)
    write_redirects(out, items, tags)
    posts = sum(1 for item in items if item.kind == "post")
    summary = {
        "Posts": str(posts),
        "Pages": str(len(items) - posts),
        "Tags": str(len(tags)),
        "Assets copied": f"{len(store.copied)} files, {store.bytes_copied / 1e6:.1f} MB",
    }
    (out / "report.md").write_text(report.render(summary), encoding="utf-8")
    return report, summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--export", type=Path, required=True)
    parser.add_argument("--content", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("."))
    args = parser.parse_args()
    report, summary = run(args.export.expanduser(), args.content.expanduser(), args.out)
    for key, value in summary.items():
        print(f"{key}: {value}")
    for category, label in Report.CATEGORIES.items():
        print(f"{label}: {report.count(category)}")


if __name__ == "__main__":
    main()
