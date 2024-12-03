import os
from bs4 import BeautifulSoup
from requests import Session
import base64

MM_BASE_URL = os.getenv("MM_BASE_URL", "https://www.school.mariamanipur.in")
MM_USERNAME = os.getenv("MM_USERNAME")
MM_PASSWORD = os.getenv("MM_PASSWORD")

USER_AGENT = (
    "Mozilla/5.0 (compatible; mm_notify/0.4; +https://github.com/sunhoww/mm_notify)"
)


def login(s: Session):
    s.post(
        f"{MM_BASE_URL}/stulogin",
        data={
            "stuenrno": MM_USERNAME,
            "stupass": MM_PASSWORD,
            "btn-submit": "true",
        },
        timeout=10,
        headers={"User-Agent": USER_AGENT},
    )


def fetch_todays_lessons_page(s: Session) -> BeautifulSoup:
    return _get_page(s, url=f"{MM_BASE_URL}/myportal/lessons")


def fetch_lesson_page(s: Session, url: str) -> BeautifulSoup:
    return _get_page(s, url=url)


def fetch_todays_notices_page(s: Session) -> BeautifulSoup:
    return _get_page(s, url=f"{MM_BASE_URL}/myportal")


def get_attachment(s: Session, url: str) -> str:
    r = s.get(url, timeout=10)
    return base64.b64encode(r.content).decode("utf-8")


def _get_page(s: Session, url: str) -> BeautifulSoup:
    r = s.get(
        url,
        timeout=10,
        headers={"User-Agent": USER_AGENT},
    )
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")
