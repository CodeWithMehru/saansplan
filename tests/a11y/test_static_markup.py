"""Static markup and frontend safety checks."""

from html.parser import HTMLParser
from pathlib import Path


class MarkupAudit(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.labels: list[str] = []
        self.controls: list[tuple[str, str | None]] = []
        self.h1 = 0
        self.inline_handlers = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if "id" in values:
            self.ids.append(str(values["id"]))
        if tag == "h1":
            self.h1 += 1
        if tag == "label" and "for" in values:
            self.labels.append(str(values["for"]))
        if tag in ("input", "select", "textarea"):
            self.controls.append((tag, values.get("id")))
        if any(name.lower().startswith("on") for name in values):
            self.inline_handlers += 1


def test_static_markup_is_accessible_and_safe() -> None:
    html = Path("app/static/index.html").read_text(encoding="utf-8")
    audit = MarkupAudit()
    audit.feed(html)
    assert audit.h1 == 1
    assert len(audit.ids) == len(set(audit.ids))
    assert audit.inline_handlers == 0
    for _tag, control_id in audit.controls:
        if control_id:
            assert (
                control_id in audit.labels
                or "aria-label=" in html
                or control_id.startswith("member-")
            )


def test_frontend_never_uses_innerhtml_for_dynamic_data() -> None:
    source = "\n".join(path.read_text(encoding="utf-8") for path in Path("app/static").glob("*.js"))
    assert "innerHTML" not in source


def test_timeline_table_has_caption_and_scoped_headers() -> None:
    html = Path("app/static/index.html").read_text(encoding="utf-8")
    assert "<caption>Hour-by-hour air quality and exposure</caption>" in html
    assert html.count('scope="col"') >= 6
