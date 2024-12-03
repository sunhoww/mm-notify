import hashlib
import logging
import requests

from kanboard import (
    create_task,
    create_task_file,
    get_project_id,
    get_task_by_reference,
)
from lessons import (
    get_lesson,
    get_lesson_urls,
    get_links,
    get_subject,
    make_category_getter,
)
from notices import get_notices
from school import (
    fetch_todays_lessons_page,
    fetch_todays_notices_page,
    get_attachment,
    login,
    fetch_lesson_page,
)


logger = logging.getLogger(__name__)
logging.basicConfig(
    format="[%(levelname)s] %(message)s",
    level=logging.INFO,
)


def _process_notices(s: requests.Session):
    soup = fetch_todays_notices_page(s)
    if soup.find(string=lambda x: "No Notice Found!" in x):
        logger.info("No Notice Found!")

    notices = get_notices(soup)
    if not notices:
        return

    logger.info(f"Notices found: {len(notices)}")

    notice_count = 0
    for notice in notices:
        reference = hashlib.md5(
            notice.get("description", "").encode(), usedforsecurity=False
        ).hexdigest()
        if get_task_by_reference(project_id=get_project_id(), reference=reference):
            continue

        notice["reference"] = reference
        task_id = create_task(**notice)
        if not task_id:
            logger.warn(f"Failed to create task for notice: {reference}")
            continue
        notice_count += 1

    logger.info(f"Notices created: {notice_count}")


def _process_lessons(s: requests.Session):
    soup = fetch_todays_lessons_page(s)
    if soup.find(string=lambda x: "No Lessons Found!" in x):
        logger.info("No Lessons Found!")

    urls = get_lesson_urls(soup)
    if not urls:
        return

    logger.info(f"Lessons found: {len(urls)}")
    get_category = make_category_getter()

    lesson_count = file_count = 0
    for url in urls:
        if get_task_by_reference(project_id=get_project_id(), reference=url):
            continue

        soup = fetch_lesson_page(s, url)
        lesson = get_lesson(soup)
        lesson["reference"] = url
        if subject := get_subject(soup):
            if category_id := get_category(subject):
                lesson["category_id"] = category_id
        task_id = create_task(**lesson)
        if not task_id:
            logger.warn(f"Failed to create task for lesson: {url}")
            continue
        lesson_count += 1

        links = get_links(soup)
        logger.info(f"Attachments found for task #{task_id}: {len(links)}")
        for href, filename in links:
            blob = get_attachment(s, href)
            task_file_id = create_task_file(
                lesson["project_id"], task_id, filename, blob
            )
            if not task_file_id:
                logger.warn(
                    f"Failed to create attachment for task #{task_id}: {filename}"
                )
                continue
            file_count += 1

    logger.info(f"Lessons created: {lesson_count}")
    logger.info(f"Attachments created: {file_count}")


def _main():
    with requests.Session() as s:
        try:
            login(s)
            _process_notices(s)
            _process_lessons(s)
        except requests.exceptions.ConnectTimeout:
            logger.error("Connection timed out.")


if __name__ == "__main__":
    _main()
