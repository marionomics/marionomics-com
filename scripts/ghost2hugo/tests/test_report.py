import pytest

from report import Report


def test_report_rejects_unknown_category():
    with pytest.raises(ValueError):
        Report().add("s", "nope", "x")


def test_report_renders_counts_and_details():
    r = Report()
    r.add("p1", "asset_removed", "/content/images/a.png")
    r.add("p1", "asset_removed", "/content/images/b.png")
    md = r.render({"Posts": "1"})
    assert "- **Posts:** 1" in md
    assert "| Removed (file not in backup) | 2 |" in md
    assert "### p1" in md
    assert "- `/content/images/b.png`" in md
    assert r.count("asset_removed") == 2 and r.count("link_rewritten") == 0
