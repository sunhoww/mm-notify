import json
import logging
import os
import re
from typing import cast, List
import requests
from bs4 import BeautifulSoup, Tag
from requests.sessions import Session
from websockets.sync.client import connect

MM_BASE_URL = "https://www.school.mariamanipur.in"
MM_USERNAME = os.getenv("MM_USERNAME")
MM_PASSWORD = os.getenv("MM_PASSWORD")

HA_WS_ENDPOINT = os.getenv("HA_WS_ENDPOINT", "")
HA_TODO_ID = os.getenv("HA_TODO_ID")
HA_TOKEN = os.getenv("HA_TOKEN")

USER_AGENT = (
    "Mozilla/5.0 (compatible; mm_notify/0.3; +https://github.com/sunhoww/mm_notify)"
)

logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(levelname)s:%(message)s",
    level=logging.INFO,
)


def get_notices(s: Session) -> List[str]:
    r = s.get(
        f"{MM_BASE_URL}/myportal",
        timeout=10,
        headers={"User-Agent": USER_AGENT},
    )

    soup = BeautifulSoup(r.text, "html.parser")
    if soup.find(string=lambda x: "No Notice Found!" in x):
        logger.info("No Notice Found!")

    notices = soup.find_all(class_="notice-board")
    if not notices:
        return []

    logger.info(f"Notice found: {len(notices)}")
    return ["\n".join([x for x in n.stripped_strings]) for n in notices]


def get_lessons(s: Session) -> List[str]:
    headers = {"User-Agent": USER_AGENT}

    r = s.get(
        f"{MM_BASE_URL}/myportal/lessons",
        timeout=10,
        headers=headers,
    )
    soup = BeautifulSoup(r.text, "html.parser")
    if soup.find(string=lambda x: "No Lessons Found!" in x):
        logger.info("No Lessons Found!")

    lessons = soup.find_all(href=re.compile("viewclass"))
    if not lessons:
        return []

    msgs = []
    logger.info(f"Lesson found: {len(lessons)}")
    for a in lessons:
        lesson = []
        l_r = s.get(a["href"], timeout=10, headers=headers)
        l_soup = BeautifulSoup(l_r.text, "html.parser")
        desc = cast(Tag, l_soup.find(class_="lesson-desc"))
        desc = cast(Tag, desc.find_parent(class_="text-center")).stripped_strings
        aside = cast(Tag, l_soup.find(class_="success-msg-box")).stripped_strings

        lesson = list(desc) + list(aside)
        if lesson:
            lesson.append(a["href"])
            msgs.append("\n".join(lesson))
        else:
            logger.warn(f'Found no lesson at {a["href"]}')

    return msgs


def update_ha(msgs: List[str]) -> None:
    with connect(HA_WS_ENDPOINT) as ws:
        id = 1
        _req = {
            "type": "auth",
            "access_token": HA_TOKEN,
        }
        ws.send(json.dumps(_req))
        ws.recv()
        ws.recv()
        _req = {
            "id": id,
            "return_response": True,
            "type": "call_service",
            "domain": "todo",
            "service": "get_items",
            "target": {"entity_id": HA_TODO_ID},
        }
        ws.send(json.dumps(_req))
        h_descriptions = [
            hash(x.get("description"))
            for x in json.loads(ws.recv())
            .get("result", {})
            .get("response", {})
            .get(HA_TODO_ID, {})
            .get("items", [])
        ]

        for msg in msgs:
            item = msg.split("\n")[0]
            description = "\n".join(msg.split("\n")[1:])
            if hash(description) not in h_descriptions:
                id += 1
                _req = {
                    "id": id,
                    "type": "call_service",
                    "domain": "todo",
                    "service": "add_item",
                    "target": {"entity_id": HA_TODO_ID},
                    "service_data": {"item": item, "description": description},
                }
                ws.send(json.dumps(_req))

                if json.loads(ws.recv()).get("success", False):
                    logger.info("Added item.")
                else:
                    logger.warn("Failed to add item.")
            else:
                logger.info("Item already exists. Not adding.")


def main():
    with requests.Session() as s:
        try:
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
            notices = get_notices(s)
            if notices:
                update_ha(notices)

            lessons = get_lessons(s)
            if lessons:
                update_ha(lessons)

        except requests.exceptions.ConnectTimeout:
            logger.error("Connection timed out.")


if __name__ == "__main__":
    main()
