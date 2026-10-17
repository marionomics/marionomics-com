import json

from check_site import (check_archive, check_index, check_landing, check_links, check_old_paths,
                        check_redirect_targets, main)

LANDING = ('<form class=nf-form></form><form class="nf-form"></form>'
           '<section id=done></section><a href=/archivo/>archivo</a>')


def _page(public, rel, html):
    path = public / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")


def _site(tmp_path, page_count=2):
    public = tmp_path / "public"
    _page(public, "index.html", LANDING + '<a href=/mi-post/>p</a><link rel=canonical href="https://marionomics.com/">')
    _page(public, "archivo/index.html", "<li>a</li><li>b</li>")
    _page(public, "mi-post/index.html",
          '<img src="/content/images/con%20espacio.png" srcset="/content/images/con%20espacio.png 600w">'
          '<a href="/tag/x/">t</a><a href="https://otro.com/">e</a><iframe src="//youtube.com/e"></iframe>')
    _page(public, "tag/x/index.html", "<a href='/'>home</a>")
    _page(public, "content/images/con espacio.png", "png")
    _page(public, "pagefind/pagefind-entry.json",
          json.dumps({"version": "1.3.0", "languages": {"es": {"hash": "h", "page_count": page_count}}}))
    return public


def test_clean_site_has_no_problems(tmp_path):
    public = _site(tmp_path)
    redirects = tmp_path / "redirects.txt"
    redirects.write_text("/mi-post/\thttps://marionomics.com/mi-post/\n"
                         "/cripto/\thttps://marionomics.com/\n"
                         "/50-recursos/\thttps://marionomics.notion.site/x\n")
    _page(public, "cripto/index.html", '<meta http-equiv=refresh content="0; url=https://marionomics.com/">')
    _page(public, "50-recursos/index.html", '<meta http-equiv=refresh content="0; url=https://marionomics.notion.site/x">')
    assert check_links(public) == []
    assert check_redirect_targets(public, redirects) == []
    assert check_index(public, 2) == []
    assert main([str(public), str(redirects), "--min-indexed", "2", "--min-archive", "2"]) == 0


def test_broken_link_and_missing_image_reported(tmp_path):
    public = _site(tmp_path)
    _page(public, "otro/index.html", '<a href="/no-existe/">x</a><img src="/content/images/falta.png">')
    problems = check_links(public)
    assert "otro/index.html: broken /no-existe/" in problems
    assert "otro/index.html: broken /content/images/falta.png" in problems


def test_missing_redirect_target_reported(tmp_path):
    public = _site(tmp_path)
    redirects = tmp_path / "redirects.txt"
    redirects.write_text("/perdido/\thttps://marionomics.com/perdido/\n")
    assert check_redirect_targets(public, redirects) == [
        "redirect target missing: /perdido/ -> https://marionomics.com/perdido/"]


def test_low_index_count_reported(tmp_path):
    public = _site(tmp_path, page_count=5)
    assert check_index(public, 332) == ["Pagefind indexed 5 pages, expected at least 332"]
    assert main([str(public), str(tmp_path / "none.txt"), "--min-indexed", "332"]) == 1


def test_old_paths_identity_alias_and_missing(tmp_path):
    public = tmp_path / "public"
    _page(public, "mi-post/index.html", "post")
    _page(public, "cripto/index.html", '<meta http-equiv=refresh content="0; url=https://marionomics.com/">')
    _page(public, "pro/index.html", "<p>se quedó una página real</p>")
    redirects = tmp_path / "redirects.txt"
    redirects.write_text("/mi-post/\thttps://marionomics.com/mi-post/\n"
                         "/cripto/\thttps://marionomics.com/\n"
                         "/pro/\thttps://marionomics.com/\n"
                         "/perdido/\thttps://marionomics.com/perdido/\n")
    assert check_old_paths(public, redirects) == [
        "old path not redirecting: /pro/ -> https://marionomics.com/",
        "old path missing: /perdido/",
    ]


def test_landing_ok_and_each_failure(tmp_path):
    public = tmp_path / "public"
    _page(public, "index.html", LANDING)
    assert check_landing(public) == []
    _page(public, "index.html", '<header class="top"></header><form class="nf-form"></form>')
    assert check_landing(public) == ["landing: missing form", "landing: missing done section",
                                     "landing: missing archive link", "landing: has blog header"]


def test_archive_count(tmp_path):
    public = tmp_path / "public"
    assert check_archive(public, 2) == ["archive missing"]
    _page(public, "archivo/index.html", "<ul><li>a</li><li>b</li></ul>")
    assert check_archive(public, 2) == []
    assert check_archive(public, 3) == ["archive lists 2 posts, expected at least 3"]
    _page(public, "archivo/index.html", "<link rel=stylesheet href=/a.css><link rel=canonical href=/><ul><li class=x>a</li></ul>")
    assert check_archive(public, 2) == ["archive lists 1 posts, expected at least 2"]
