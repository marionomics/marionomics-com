import pytest
import yaml

from builders import ghost_data, ghost_post, write_export
from emit import to_mexico
from ghost2hugo import run


def _repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "hugo.toml").write_text("")
    return repo


def _front_matter(path):
    return yaml.safe_load(path.read_text(encoding="utf-8").split("---\n")[1])


def test_date_uses_mexico_city_time():
    assert to_mexico("2025-06-21T01:03:00.000Z") == "2025-06-20T19:03:00-06:00"
    assert to_mexico("2022-03-01T12:00:00.000Z") == "2022-03-01T06:00:00-06:00"


def test_run_end_to_end(tmp_path):
    repo = _repo(tmp_path)
    content = tmp_path / "ghost-content"
    (content / "images/2025/06").mkdir(parents=True)
    (content / "images/2025/06/a.png").write_bytes(b"png")
    post = ghost_post(
        slug="mi-post",
        html=(
            '<p>Ver <a href="__GHOST_URL__/otro/">otro</a> y $x_i$.</p>'
            '<figure class="kg-card kg-image-card"><img src="__GHOST_URL__/content/images/2025/06/a.png"></figure>'
            '<figure class="kg-card kg-image-card"><img src="__GHOST_URL__/content/images/2021/viejo.png"></figure>'
        ),
        custom_excerpt="Subtítulo",
        feature_image="__GHOST_URL__/content/images/2025/06/a.png",
    )
    other = ghost_post(slug="otro", published_at="2024-01-01T00:00:00.000Z")
    page = ghost_post(slug="about-2", type="page", title="La economía con manzanitas")
    data = ghost_data(
        [post, other, page],
        tags=[{"id": "t1", "slug": "econometria", "name": "Econometría", "visibility": "public"}],
        posts_tags=[{"id": "x", "post_id": post["id"], "tag_id": "t1", "sort_order": 0}],
    )

    report, summary = run(write_export(tmp_path, data), content, repo)

    post_file = repo / "content/posts/mi-post.html"
    fm = _front_matter(post_file)
    assert fm["title"] == "Título de prueba"
    assert fm["subtitle"] == "Subtítulo" and fm["description"] == "Subtítulo"
    assert fm["date"] == "2025-06-20T19:03:00-06:00"
    assert fm["tags"] == ["econometria"]
    assert fm["math"] is True and fm["twitter"] is False
    assert fm["feature_image"] == "/content/images/2025/06/a.png"
    body = post_file.read_text(encoding="utf-8")
    assert 'href="/otro/"' in body and r"\(x_i\)" in body and "viejo.png" not in body
    assert (repo / "static/content/images/2025/06/a.png").is_file()

    page_fm = _front_matter(repo / "content/pages/about-2.html")
    assert "tags" not in page_fm and page_fm["title"] == "La economía con manzanitas"
    assert _front_matter(repo / "content/tags/econometria/_index.md") == {"title": "Econometría"}

    redirects = (repo / "redirects.txt").read_text(encoding="utf-8").splitlines()
    assert "/mi-post/\thttps://blog.marionomics.com/mi-post/" in redirects
    assert "/about-2/\thttps://blog.marionomics.com/about-2/" in redirects
    assert "/tag/econometria/\thttps://blog.marionomics.com/tag/econometria/" in redirects
    assert "/cripto/\thttps://blog.marionomics.com/" in redirects
    assert any(line.startswith("/50-recursos-para-econometria/\thttps://marionomics.notion.site/")
               for line in redirects)

    assert summary["Posts"] == "2" and summary["Pages"] == "1" and summary["Tags"] == "1"
    assert "/content/images/2021/viejo.png" in (repo / "report.md").read_text(encoding="utf-8")


def test_description_falls_back_to_plaintext(tmp_path):
    repo = _repo(tmp_path)
    long_text = "palabra " * 60
    run(write_export(tmp_path, ghost_data([ghost_post(slug="p", plaintext=long_text)])), tmp_path / "x", repo)
    fm = _front_matter(repo / "content/posts/p.html")
    assert fm["description"].endswith("…") and len(fm["description"]) <= 160
    assert "subtitle" not in fm and "feature_image" not in fm


def test_rerun_removes_stale_outputs(tmp_path):
    repo = _repo(tmp_path)
    stale = repo / "content/posts/borrado.html"
    stale.parent.mkdir(parents=True)
    stale.write_text("x")
    stale_img = repo / "static/content/images/viejo.png"
    stale_img.parent.mkdir(parents=True)
    stale_img.write_text("x")
    keep = repo / "content/search.md"
    keep.write_text("x")
    run(write_export(tmp_path, ghost_data([ghost_post(slug="nuevo")])), tmp_path / "empty", repo)
    assert not stale.exists() and not stale_img.exists()
    assert keep.exists() and (repo / "content/posts/nuevo.html").exists()


def test_refuses_non_repo_out(tmp_path):
    with pytest.raises(SystemExit):
        run(write_export(tmp_path, ghost_data([])), tmp_path, tmp_path / "no-repo")
