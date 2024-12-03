from bs4 import BeautifulSoup
from datetime import date, datetime
from typing import Callable, List, Tuple, cast

from kanboard import TaskBase, get_all_categories, get_project_id
from utils import get_column_id, md

KB_COLUMN_TITLE = "Ready"


def get_lesson(soup: BeautifulSoup) -> TaskBase:
    lesson: TaskBase = {
        "title": _get_title(soup),
        "project_id": get_project_id(),
        "column_id": get_column_id(KB_COLUMN_TITLE),
        "description": _get_description(soup),
        "date_started": _get_date_started(soup) or date.today().isoformat(),
    }

    return lesson


def get_lesson_urls(soup: BeautifulSoup) -> List[str]:
    content = soup.select("section.contents-wrap div.lessons-grids div.lesson-topic a")
    return [cast(str, x["href"]) for x in content]


def get_links(soup: BeautifulSoup) -> List[Tuple[str, str]]:
    content = soup.select_one("section.contents-wrap div.instructions-box")
    assert content is not None
    return [
        (cast(str, x["href"]), x.get_text(strip=True))
        for x in soup.select("section.contents-wrap div.assignments-wrap a")
        + soup.select("section.contents-wrap div.success-msg-box a")
    ]


def make_category_getter() -> Callable[[str], int | None]:
    categories = get_all_categories(project_id=get_project_id())

    def _get_category(name: str) -> int | None:
        for category in categories:
            if category["name"] == name:
                return category["id"]
        return None

    return _get_category


def _get_title(soup: BeautifulSoup) -> str:
    try:
        content = soup.select_one("section.contents-wrap div.lesson-desc")
        assert content is not None
        return content.get_text(strip=True)
    except AssertionError:
        return ""


def _get_description(soup: BeautifulSoup) -> str:
    try:
        content = soup.select_one("section.contents-wrap div.instructions-box")
        assert content is not None
        links = get_links(soup)
        if links:
            p = soup.new_tag("p")
            p.string = "Attachments"
            content.append(p)
            ul = soup.new_tag("ul")
            content.append(ul)
            for href, string in links:
                a = soup.new_tag("a", href=href)
                a.string = string
                li = soup.new_tag("li")
                li.append(a)
                ul.append(li)
        if author := _get_author(soup):
            p = soup.new_tag("p")
            i = soup.new_tag("i")
            i.string = author
            p.append(i)
            content.append(p)
        description = md(content).strip()
        return description
    except AssertionError:
        return ""


def _get_lesson_credit(soup: BeautifulSoup, index: int) -> str | None:
    try:
        content = soup.select_one("section.contents-wrap p.lesson-credit")
        assert content is not None
        return content.get_text(strip=True).split(" // ")[index]
    except (AssertionError, IndexError):
        return None


def _get_date_started(soup: BeautifulSoup) -> str | None:
    text = _get_lesson_credit(soup, 0)
    if text:
        return datetime.strptime(text, "%d-%b-%Y").date().isoformat()
    return None


def get_subject(soup: BeautifulSoup) -> str | None:
    return _get_lesson_credit(soup, 1)


def _get_author(soup: BeautifulSoup) -> str | None:
    return _get_lesson_credit(soup, 2)
