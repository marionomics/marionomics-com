import json

from check_site import check_index, check_links, check_redirect_targets, main


def _page(public, rel, html):
    path = public / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")


def _site(tmp_path, page_count=2):
    public = tmp_path / "public"
    _page(public, "index.html", '<a href=/mi-post/>p</a><link rel=canonical href="https://blog.marionomics.com/">')
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
    redirects.write_text("/mi-post/\thttps://blog.marionomics.com/mi-post/\n"
                         "/cripto/\thttps://blog.marionomics.com/\n"
                         "/50-recursos/\thttps://marionomics.notion.site/x\n")
    assert check_links(public) == []
    assert check_redirect_targets(public, redirects) == []
    assert check_index(public, 2) == []
    assert main([str(public), str(redirects), "--min-indexed", "2"]) == 0


def test_broken_link_and_missing_image_reported(tmp_path):
    public = _site(tmp_path)
    _page(public, "otro/index.html", '<a href="/no-existe/">x</a><img src="/content/images/falta.png">')
    problems = check_links(public)
    assert "otro/index.html: broken /no-existe/" in problems
    assert "otro/index.html: broken /content/images/falta.png" in problems


def test_missing_redirect_target_reported(tmp_path):
    public = _site(tmp_path)
    redirects = tmp_path / "redirects.txt"
    redirects.write_text("/perdido/\thttps://blog.marionomics.com/perdido/\n")
    assert check_redirect_targets(public, redirects) == [
        "redirect target missing: /perdido/ -> https://blog.marionomics.com/perdido/"]


def test_low_index_count_reported(tmp_path):
    public = _site(tmp_path, page_count=5)
    assert check_index(public, 332) == ["Pagefind indexed 5 pages, expected at least 332"]
    assert main([str(public), str(tmp_path / "none.txt"), "--min-indexed", "332"]) == 1
