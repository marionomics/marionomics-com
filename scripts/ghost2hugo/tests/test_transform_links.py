from report import Report
from transform import (
    normalize_urls,
    parse,
    replace_membership_cards,
    rewrite_internal_links,
    rewrite_portal_links,
)


def test_ghost_origins_become_root_relative():
    soup = parse(
        '<a href="__GHOST_URL__/mi-post/">a</a>'
        '<img src="https://www.marionomics.com/content/images/a.png" '
        'srcset="https://marionomics.com/content/images/size/w600/a.png 600w, /content/images/a.png 1000w">'
        '<a href="https://marionomics.com.mx/x">otro dominio</a>'
        '<a href="https://app.marionomics.com/curso">app</a>'
    )
    normalize_urls(soup)
    a, img, other, app = soup.find_all(["a", "img"])
    assert a["href"] == "/mi-post/"
    assert img["src"] == "/content/images/a.png"
    assert img["srcset"] == "/content/images/size/w600/a.png 600w, /content/images/a.png 1000w"
    assert other["href"] == "https://marionomics.com.mx/x"
    assert app["href"] == "https://app.marionomics.com/curso"


def test_bare_ghost_url_becomes_root():
    soup = parse('<a href="__GHOST_URL__">inicio</a><a href="__GHOST_URL__#/portal/signup">s</a>')
    normalize_urls(soup)
    assert [a["href"] for a in soup.find_all("a")] == ["/", "/#/portal/signup"]


def test_portal_links_go_to_substack():
    soup = parse('<a href="/#/portal/signup">s</a><a href="#/portal/account/plans">p</a>')
    rewrite_portal_links(soup)
    assert {a["href"] for a in soup.find_all("a")} == {"https://marionomics.substack.com/subscribe"}


def test_internal_links():
    report = Report()
    soup = parse(
        '<a href="/conocido/">1</a><a href="/conocido/#seccion">2</a><a href="/conocido?ref=x">3</a>'
        '<a href="/tag/python/">4</a><a href="/tag/borrada/">5</a><a href="/cripto/">6</a>'
        '<a href="/content/files/a.pdf">7</a><a href="/tools/x/">8</a>'
        '<a href="https://otro.com/">9</a><a href="#nota">10</a><a href="/">11</a>'
    )
    rewrite_internal_links(soup, "este-post", {"conocido"}, {"python"}, report)
    assert [a["href"] for a in soup.find_all("a")] == [
        "/conocido/", "/conocido/#seccion", "/conocido/", "/tag/python/", "/", "/",
        "/content/files/a.pdf", "/tools/x/", "https://otro.com/", "#nota", "/",
    ]
    assert report.entries["este-post"]["link_rewritten"] == ["/tag/borrada/", "/cripto/"]


def test_membership_cards_become_substack_note():
    soup = parse(
        '<p>antes</p><div class="kg-card kg-signup-card"><form></form></div>'
        '<div class="kg-card kg-product-card">x</div>'
    )
    replace_membership_cards(soup)
    notes = soup.select("p.substack-note a")
    assert len(notes) == 2
    assert notes[0]["href"] == "https://marionomics.substack.com"
    assert notes[0].get_text() == "Escribo cada semana en Substack →"
    assert not soup.select(".kg-signup-card, .kg-product-card")


def test_internal_links_ignore_case_and_trailing_junk():
    report = Report()
    soup = parse(
        '<a href="/IA-Puede-Reducir/">1</a>'
        '<a href="/conocido/https://marionomics.com/conocido/">2</a>'
        '<a href="/Conocido/#parte">3</a>'
    )
    rewrite_internal_links(soup, "este-post", {"ia-puede-reducir", "conocido"}, set(), report)
    assert [a["href"] for a in soup.find_all("a")] == ["/ia-puede-reducir/", "/conocido/", "/conocido/#parte"]
    assert "este-post" not in report.entries
