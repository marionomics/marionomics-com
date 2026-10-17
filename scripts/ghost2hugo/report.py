"""Collects per-post conversion issues and renders report.md."""
from collections import defaultdict


class Report:
    CATEGORIES = {
        "asset_removed": "Removed (file not in backup)",
        "feature_image_missing": "Feature image dropped (file not in backup)",
        "link_rewritten": "Link to non-migrated page rewritten to /",
        "math_left_as_text": "$…$ left as text",
        "code_injection": "Unexpected code injection dropped",
        "inline_script": "Inline script removed",
        "unknown_card": "Unknown Ghost card type",
    }

    def __init__(self):
        self.entries = defaultdict(lambda: defaultdict(list))

    def add(self, slug: str, category: str, detail: str) -> None:
        if category not in self.CATEGORIES:
            raise ValueError(f"unknown report category: {category}")
        self.entries[slug][category].append(detail)

    def count(self, category: str) -> int:
        return sum(len(cats.get(category, [])) for cats in self.entries.values())

    def render(self, summary: dict[str, str]) -> str:
        lines = ["# Ghost import report", "", "## Summary", ""]
        lines += [f"- **{key}:** {value}" for key, value in summary.items()]
        lines += ["", "| Issue | Count |", "|---|---|"]
        lines += [f"| {label} | {self.count(cat)} |" for cat, label in self.CATEGORIES.items()]
        lines += ["", "## By post", ""]
        for slug in sorted(self.entries):
            lines += [f"### {slug}", ""]
            for cat, details in self.entries[slug].items():
                lines.append(f"**{self.CATEGORIES[cat]}**")
                lines += [f"- `{detail}`" for detail in details]
                lines.append("")
        return "\n".join(lines) + "\n"
