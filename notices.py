from bs4 import BeautifulSoup, Tag
from datetime import date, datetime
from typing import List

from kanboard import TaskBase, get_project_id
from utils import get_column_id, md

KB_COLUMN_TITLE = "Backlog"


def get_notices(soup: BeautifulSoup) -> List[TaskBase]:
    contents = soup.select("section.contents-wrap div.notice-board")
    return [_get_notice(x) for x in contents]


def _get_notice(tag: Tag) -> TaskBase:
    notice: TaskBase = {
        "title": _get_title(tag),
        "project_id": get_project_id(),
        "column_id": get_column_id(KB_COLUMN_TITLE),
        "description": _get_description(tag),
        "date_started": _get_date_started(tag) or date.today().isoformat(),
    }

    return notice


def _get_title(tag: Tag) -> str:
    try:
        content = tag.select_one("p.text-warning")
        assert content is not None
        return content.get_text(strip=True)
    except AssertionError:
        return ""


def _get_description(tag: Tag) -> str:
    try:
        title = tag.select_one("p.text-warning")
        assert title is not None
        title.clear()
        return md(tag).strip()
    except AssertionError:
        return ""


def _get_date_started(tag: Tag) -> str | None:
    try:
        content = tag.select_one("p.text-warning")
        assert content is not None
        text = content.get_text(strip=True).split(" / ")[0]
        if text:
            return datetime.strptime(text, "%d-%b-%Y").date().isoformat()
    except (AssertionError, IndexError):
        pass

    return None
