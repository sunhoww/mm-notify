import os
from typing import List, Required, Tuple, TypedDict, Unpack
from random import randrange
import requests
from requests.auth import HTTPBasicAuth

KB_PROJECT_ID = int(os.getenv("KB_PROJECT_ID", "1"))
KB_BASE_URL = os.getenv("KB_BASE_URL")
KB_USERNAME = os.getenv("KB_USERNAME")
KB_API_TOKEN = os.getenv("KB_API_TOKEN")


class CategoryBase(TypedDict, total=False):
    project_id: Required[int]
    name: Required[str]
    color_id: str
    description: str


class Category(CategoryBase):
    id: Required[int]


class CategoryParams(TypedDict):
    project_id: int


class ColumnBase(TypedDict, total=False):
    project_id: Required[int]
    title: Required[str]
    task_limit: int
    description: str


class Column(ColumnBase):
    id: Required[int]
    position: int
    hide_in_dashboard: int


class TaskBase(TypedDict, total=False):
    title: Required[str]
    project_id: Required[int]
    color_id: str
    column_id: int
    owner_id: int
    creator_id: int
    date_due: str
    description: str
    category_id: int
    score: int
    swimlane_id: int
    priority: int
    recurrence_status: int
    recurrence_trigger: int
    recurrence_factor: int
    recurrence_timeframe: int
    recurrence_basedate: int
    reference: str
    tags: List[str]
    date_started: str


class Task(TaskBase):
    id: Required[str]


class TaskParams(TaskBase):
    pass


class TaskByReferenceParams(TypedDict):
    project_id: int
    reference: str


class TaskFileBase(TypedDict):
    project_id: int
    task_id: int
    filename: int
    blob: str


class TaskFile(TaskFileBase, total=False):
    id: Required[int]
    name: str
    path: str
    is_image: int
    date: int
    user_id: int
    size: int
    username: str
    etag: str


class TaskFileParams(TaskFileBase):
    pass


class KanboardRequest[T](TypedDict):
    jsonrpc: str
    method: str
    id: int
    params: T


class KanboardResponse[T](TypedDict):
    jsonrpc: str
    id: int
    result: T


def _request[P, T](method: str, params: P) -> T:
    if not KB_BASE_URL or not KB_USERNAME or not KB_API_TOKEN:
        raise ValueError

    payload: KanboardRequest[P] = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": randrange(1, 10**6),
    }
    r = requests.post(
        url=f"{KB_BASE_URL}/jsonrpc.php",
        json=payload,
        auth=HTTPBasicAuth(KB_USERNAME, KB_API_TOKEN),
    )
    r.raise_for_status()
    result: KanboardResponse[T] = r.json()
    return result["result"]


def get_project_id() -> int:
    return KB_PROJECT_ID


def get_all_categories(**args: Unpack[CategoryParams]) -> List[Category]:
    return _request(method="getAllCategories", params=args)


def get_columns(*args: Unpack[Tuple[int]]) -> List[Column]:
    return _request(method="getColumns", params=args)


def get_task_by_reference(**args: Unpack[TaskByReferenceParams]) -> Task | None:
    return _request(method="getTaskByReference", params=args)


def create_task(**args: Unpack[TaskParams]) -> int | None:
    return _request(method="createTask", params=args)


def create_task_file(
    project_id: int, task_id: int, filename: str, blob: str
) -> int | None:
    return _request(
        method="createTaskFile", params=[project_id, task_id, filename, blob]
    )
