from report import Report
from transform import (
    check_code_injection,
    convert_inline_math,
    detect_flags,
    handle_scripts,
    normalize_code_languages,
    parse,
    report_unknown_cards,
)


def test_inline_math_converted_and_prices_untouched():
    r = Report()
    soup = parse(
        "<p>Sea $D_{g,t}$ un indicador, $n$ el tamaño y $(g,t)$ el par. "
        "Cuesta $400 y $500. Pagas $US 5 o $MXN 90. De $5 mil a $10 mil.</p>"
        "<p>$$ x^2 $$</p>"
    )
    convert_inline_math(soup, "p", r)
    text = soup.get_text()
    assert r"\(D_{g,t}\)" in text and r"\(n\)" in text and r"\((g,t)\)" in text
    assert "Cuesta $400 y $500." in text
    assert "Pagas $US 5 o $MXN 90." in text
    assert "De $5 mil a $10 mil." in text
    assert "$$ x^2 $$" in text
    assert "p" not in r.entries


def test_dollars_in_code_are_never_math():
    soup = parse('<pre><code class="language-r">df$a$b + df$x</code></pre><p><code>$n$</code></p>')
    convert_inline_math(soup, "p", Report())
    assert soup.find("pre").get_text() == "df$a$b + df$x"
    assert soup.find("p").get_text() == "$n$"


def test_non_latex_pair_is_reported():
    r = Report()
    soup = parse("<p>Precio en $hola mundo$ ayer</p>")
    convert_inline_math(soup, "p", r)
    assert soup.get_text() == "Precio en $hola mundo$ ayer"
    assert r.entries["p"]["math_left_as_text"] == ["$hola mundo$"]


def test_code_languages_normalized():
    soup = parse(
        '<pre><code class="language-Python">x</code></pre>'
        '<pre><code class="language-HTML">x</code></pre>'
        '<pre><code class="language-Terminal">x</code></pre>'
        '<pre><code class="language-chatGPT">x</code></pre>'
        '<pre><code class="language-r">x</code></pre>'
    )
    normalize_code_languages(soup)
    assert [c["class"] for c in soup.find_all("code")] == [
        ["language-python"], ["language-markup"], ["language-bash"], ["language-none"], ["language-r"],
    ]


def test_twitter_script_removed_other_scripts_reported():
    r = Report()
    soup = parse(
        '<figure class="kg-card kg-embed-card"><blockquote class="twitter-tweet">'
        '<a href="https://twitter.com/x">t</a></blockquote>'
        '<script async src="https://platform.twitter.com/widgets.js"></script></figure>'
        '<script src="https://example.com/e.js"></script>'
    )
    handle_scripts(soup, "p", r)
    assert [s.get("src") for s in soup.find_all("script")] == ["https://example.com/e.js"]
    assert r.entries["p"]["inline_script"] == ["https://example.com/e.js"]
    assert detect_flags(soup) == {"math": False, "twitter": True}


def test_math_flag():
    assert detect_flags(parse(r"<p>\(x\)</p>"))["math"] is True
    assert detect_flags(parse(r"<p>\[x\]</p>"))["math"] is True
    assert detect_flags(parse("<p>$$x$$</p>"))["math"] is True
    assert detect_flags(parse("<pre><code>$$x$$</code></pre><p>$400</p>"))["math"] is False


def test_known_code_injection_is_silent_unknown_is_reported():
    r = Report()
    check_code_injection(
        '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.10.1/dist/katex.css">'
        '<script defer src="https://cdn.jsdelivr.net/npm/katex@0.10.1/dist/contrib/auto-render.min.js"></script>'
        '<script>document.addEventListener("DOMContentLoaded", function(){ renderMathInElement(document.body); });</script>'
        '<!-- prism -->'
        '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.25.0/themes/prism-dark.min.css">',
        "a", r)
    check_code_injection("<style>.x{color:red}</style>", "b", r)
    check_code_injection("", "c", r)
    assert "a" not in r.entries and "c" not in r.entries
    assert r.entries["b"]["code_injection"] == ["<style>.x{color:red}</style>"]


def test_unknown_cards_reported():
    r = Report()
    soup = parse('<div class="kg-card kg-callout-card"></div><div class="kg-card kg-mystery-card"></div>')
    report_unknown_cards(soup, "p", r)
    assert r.entries["p"]["unknown_card"] == ["kg-mystery-card"]
