from markdownify import MarkdownConverter

from kanboard import get_columns, get_project_id


def md(soup, **options):
    return MarkdownConverter(**options).convert_soup(soup)


def get_column_id(title: str) -> int:
    project_id = get_project_id()
    columns = get_columns(project_id)
    for column in columns:
        if column["title"] == title:
            return column["id"]

    return 1
