import json
import logging
import os
from typing import List
import requests
from bs4 import BeautifulSoup
from websockets.sync.client import connect

MM_BASE_URL = "https://www.school.mariamanipur.in"
MM_USERNAME = os.getenv("MM_USERNAME")
MM_PASSWORD = os.getenv("MM_PASSWORD")

HA_WS_ENDPOINT = os.getenv("HA_WS_ENDPOINT", "")
HA_TODO_ID = os.getenv("HA_TODO_ID")
HA_TOKEN = os.getenv("HA_TOKEN")

USER_AGENT = (
    "Mozilla/5.0 (compatible; mm_notify/0.2; +https://github.com/sunhoww/mm_notify)"
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
        todos = [
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
            if hash(description) not in todos:
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
    msgs = get_notice()
    if not msgs:
        return

    update_ha(msgs)


if __name__ == "__main__":
    main()
