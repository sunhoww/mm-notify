import hashlib
import logging
import os
from typing import List
import requests
from bs4 import BeautifulSoup

MM_BASE_URL = "https://www.school.mariamanipur.in"
MM_USERNAME = os.getenv("MM_USERNAME")
MM_PASSWORD = os.getenv("MM_PASSWORD")

HA_BASE_URL = os.getenv("HA_BASE_URL", "")
HA_NOTICE_ID = os.getenv("HA_NOTICE_ID")
HA_TODO_ID = os.getenv("HA_TODO_ID")
HA_TOKEN = os.getenv("HA_TOKEN")

USER_AGENT = (
    "Mozilla/5.0 (compatible; mm_notify/0.1; +https://github.com/sunhoww/mm_notify)"
)

logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(levelname)s:%(message)s",
    level=logging.INFO,
)


def get_notice() -> List[str]:
    with requests.Session() as s:
        msgs = []
        try:
            headers = {"User-Agent": USER_AGENT}
            s.post(
                f"{MM_BASE_URL}/stulogin",
                data={
                    "stuenrno": MM_USERNAME,
                    "stupass": MM_PASSWORD,
                    "btn-submit": "true",
                },
                timeout=10,
                headers=headers,
            )
            r = s.get(
                f"{MM_BASE_URL}/myportal",
                timeout=10,
                headers=headers,
            )

            soup = BeautifulSoup(r.text, "html.parser")
            if soup.find(string=lambda x: "No Notice Found!" in x):
                logger.info("No Notice Found!")

            for n in soup.find_all(class_="notice-board"):
                msgs.append("\n".join([x for x in n.stripped_strings]))
        except requests.exceptions.ConnectTimeout:
            logger.warning("Connection timed out.")
        finally:
            return msgs


def update_ha(msgs: List[str]) -> None:
    if not (HA_NOTICE_ID and HA_TODO_ID):
        raise Exception("Required env not found")

    headers = {
        "Authorization": f"Bearer {HA_TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
    }
    notice_ep = f"{HA_BASE_URL}/api/states/{HA_NOTICE_ID}"
    todo_ep = f"{HA_BASE_URL}/api/services/todo/add_item"
    h_msg = hashlib.shake_128("\n\n".join(msgs).encode()).hexdigest(16)

    r = requests.get(notice_ep, headers=headers)
    prev_state = r.json().get("state")

    if prev_state == h_msg:
        logger.info("Not updating ha.")
        return

    for msg in msgs:
        item = msg.split("\n")[0]
        description = "\n".join(msg.split("\n")[1:])
        r = requests.post(
            todo_ep,
            headers=headers,
            json={
                "entity_id": HA_TODO_ID,
                "item": item,
                "description": description,
            },
        )
        if r.ok:
            logger.info(f"Added - {item}")
        else:
            logger.warn("Unable to add item.")

    requests.post(notice_ep, headers=headers, json={"state": h_msg})
    logger.info("Updated ha state.")


def main():
    msgs = get_notice()
    if not msgs:
        return

    print(msgs)

    # update_ha(msgs)


if __name__ == "__main__":
    main()
