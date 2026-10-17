from assets import process_assets
from builders import make_store
from report import Report
from transform import parse


def test_resolve_exact_original_and_encoded(tmp_path):
    store = make_store(tmp_path, ["images/2025/06/a.png", "images/2025/06/con espacio ñ.png"])
    assert store.resolve("/content/images/2025/06/a.png").name == "a.png"
    assert store.resolve("/content/images/size/w600/2025/06/a.png").name == "a.png"
    assert store.resolve("/content/images/size/w1000/format/webp/2025/06/a.png").name == "a.png"
    assert store.resolve("/content/images/2025/06/con%20espacio%20%C3%B1.png").name == "con espacio ñ.png"
    assert store.resolve("/content/images/2022/01/falta.png") is None
    assert store.resolve("/otra/cosa.png") is None


def test_copy_keeps_url_path(tmp_path):
    store = make_store(tmp_path, ["images/2025/06/a.png"])
    assert store.copy("/content/images/size/w600/2025/06/a.png") is True
    assert (tmp_path / "static/content/images/size/w600/2025/06/a.png").is_file()
    assert store.copy("/content/images/size/w600/2025/06/a.png") is True
    assert store.bytes_copied == 10
    assert store.copy("/content/images/no.png") is False


def test_missing_image_removes_whole_figure(tmp_path):
    r = Report()
    soup = parse(
        '<p>a</p><figure class="kg-card kg-image-card kg-card-hascaption">'
        '<img src="/content/images/2022/x.png"><figcaption>Cap</figcaption></figure><p>b</p>'
    )
    process_assets(soup, make_store(tmp_path), "p", r)
    assert str(soup) == "<p>a</p><p>b</p>"
    assert r.entries["p"]["asset_removed"] == ["/content/images/2022/x.png"]


def test_found_image_kept_and_srcset_pruned(tmp_path):
    store = make_store(tmp_path, ["images/2025/a.png"])
    soup = parse(
        '<img src="/content/images/2025/a.png" '
        'srcset="/content/images/2025/b.png 600w, /content/images/size/w1000/2025/a.png 1000w" sizes="100vw">'
    )
    process_assets(soup, store, "p", Report())
    assert soup.img["src"] == "/content/images/2025/a.png"
    assert soup.img["srcset"] == "/content/images/size/w1000/2025/a.png 1000w"
    assert (tmp_path / "static/content/images/size/w1000/2025/a.png").is_file()


def test_srcset_removed_when_nothing_left(tmp_path):
    soup = parse('<img src="/content/images/a.png" srcset="/content/images/b.png 600w" sizes="100vw">')
    process_assets(soup, make_store(tmp_path, ["images/a.png"]), "p", Report())
    assert not soup.img.has_attr("srcset") and not soup.img.has_attr("sizes")


def test_gallery_loses_missing_images_and_disappears_when_empty(tmp_path):
    soup = parse(
        '<figure class="kg-card kg-gallery-card"><div class="kg-gallery-container"><div class="kg-gallery-row">'
        '<div class="kg-gallery-image"><img src="/content/images/ok.png"></div>'
        '<div class="kg-gallery-image"><img src="/content/images/no.png"></div></div></div></figure>'
        '<figure class="kg-card kg-gallery-card"><div class="kg-gallery-image">'
        '<img src="/content/images/no2.png"></div></figure>'
    )
    process_assets(soup, make_store(tmp_path, ["images/ok.png"]), "p", Report())
    assert [i["src"] for i in soup.find_all("img")] == ["/content/images/ok.png"]
    assert len(soup.select(".kg-gallery-card")) == 1


def test_missing_file_card_removed_bare_link_unwrapped(tmp_path):
    soup = parse(
        '<div class="kg-card kg-file-card"><a href="/content/files/2022/guia.pdf">Guía</a></div>'
        '<p>Lee <a href="/content/files/2022/otra.pdf">esta guía</a>.</p>'
    )
    process_assets(soup, make_store(tmp_path), "p", Report())
    assert str(soup) == "<p>Lee esta guía.</p>"


def test_missing_video_card_removed(tmp_path):
    soup = parse(
        '<figure class="kg-card kg-video-card"><div class="kg-video-container">'
        '<video src="/content/media/2023/v.mp4" poster="https://img.spacergif.org/v1/1x1/0a/spacer.png">'
        '</video></div></figure><p>x</p>'
    )
    process_assets(soup, make_store(tmp_path), "p", Report())
    assert str(soup) == "<p>x</p>"


def test_external_images_untouched(tmp_path):
    soup = parse('<img src="https://images.unsplash.com/photo-1">')
    process_assets(soup, make_store(tmp_path), "p", Report())
    assert soup.img["src"] == "https://images.unsplash.com/photo-1"
