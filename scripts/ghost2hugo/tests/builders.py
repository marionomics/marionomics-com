"""Helpers that build minimal Ghost export structures for tests."""
import json


def ghost_post(**overrides):
    slug = overrides.get("slug", "post")
    post = {
        "id": f"id-{slug}",
        "title": "Título de prueba",
        "slug": slug,
        "type": "post",
        "status": "published",
        "visibility": "public",
        "html": "<p>Hola</p>",
        "plaintext": "Hola",
        "published_at": "2025-06-21T01:03:00.000Z",
        "updated_at": "2025-06-22T00:00:00.000Z",
        "custom_excerpt": None,
        "feature_image": None,
        "codeinjection_head": None,
        "codeinjection_foot": None,
    }
    post.update(overrides)
    return post


def ghost_data(posts, tags=(), posts_tags=(), posts_meta=()):
    return {
        "posts": list(posts),
        "tags": list(tags),
        "posts_tags": list(posts_tags),
        "posts_meta": list(posts_meta),
    }


def write_export(tmp_path, data, fmt="backup"):
    raw = {"meta": {}, "data": data} if fmt == "backup" else {"db": [{"meta": {}, "data": data}]}
    path = tmp_path / f"export-{fmt}.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    return path


def make_store(tmp_path, files=()):
    from assets import AssetStore

    content = tmp_path / "ghost-content"
    for rel in files:
        p = content / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"x" * 10)
    return AssetStore(content, tmp_path / "static")
