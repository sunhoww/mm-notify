import logging
import os
import requests
from bs4 import BeautifulSoup

MM_BASE_URL = "https://www.school.mariamanipur.in"
MM_USERNAME = os.getenv("MM_USERNAME")
MM_PASSWORD = os.getenv("MM_PASSWORD")

HA_ENDPOINT = os.getenv("HA_ENDPOINT", "")
HA_TOKEN = os.getenv("HA_TOKEN")

USER_AGENT = "mm-notify/0.1"

logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(levelname)s:%(message)s",
    level=logging.INFO,
)


def get_notice() -> str:
    with requests.Session() as s:
        msg = []
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

            msg = []
            for n in soup.find_all(class_="notice-board"):
                msg.append("\n".join([x for x in n.stripped_strings]))
        except requests.exceptions.ConnectTimeout:
            logger.warn("Connection timed out.")
        finally:
            return "\n\n".join(msg)


def update_ha(msg):
    headers = {
        "Authorization": f"Bearer {HA_TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
    }
    r = requests.get(HA_ENDPOINT, headers=headers)
    prev_state = r.json().get("state")

    if prev_state == msg:
        logger.info("Not updating ha.")
        return

    payload = {"state": msg}
    requests.post(HA_ENDPOINT, headers=headers, json=payload)
    logger.info("Updated ha state.")


def main():
    msg = get_notice()
    if not msg:
        return

    update_ha(msg)


if __name__ == "__main__":
    main()
