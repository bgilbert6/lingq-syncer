import multiprocessing
import threading
from dataclasses import dataclass, field
from multiprocessing.context import Process
from queue import Queue
from typing import List

import aqt
import requests as http
from aqt import mw
from aqt.utils import showInfo


@dataclass
class VocabRetrieveResult:
    success: bool = False
    cards: list = field(default_factory=list)
    courses: list = field(default_factory=list)


@dataclass
class CardPageResult:
    status: int = 0
    exception: Exception = None
    cards: list = field(default_factory=list)


class UnauthorizedException(Exception):
    pass


class UnexpectedResponseException(Exception):
    pass


class NotFoundException(Exception):
    pass


def get_all_cards(api_key):
    languages = get_active_languages(api_key)
    config = mw.addonManager.getConfig(__name__)
    statuses = config["included_statuses"]

    result = VocabRetrieveResult(success=True, cards=[], courses=[])

    for language in languages:
        result.cards = get_cards(api_key, "", language, statuses)

        courses = []

        if config["include_lesson_tags"] is True:

            courses = get_courses(api_key, language)

            for course in courses:
                lessons = get_lessons(api_key, language, course["id"])
                course['lessons'] = lessons

                threads = []

                for lesson in lessons:
                    thread = threading.Thread(target=assign_card_ids, args=(api_key, language, lesson, statuses))  # Create a Thread
                    thread.start()  # Start it
                    threads.append(thread)  # Add it to a thread list

                for th in threads:
                    th.join()  # Wait for all threads to finish


        result.courses = courses
        result.success = True

        return result


def assign_card_ids(api_key, language, lesson, statuses):
    cards = get_cards(api_key, lesson['id'], language, statuses)
    lesson["card_ids"] = []

    for card in cards:
        lesson["card_ids"].append(str(card["pk"]))


def get_cards(api_key, content_id, language, statuses):
    page_batch_size = 10

    cards = []

    last_page = 1

    running = True
    has_error = False

    while running:
        results = Queue()
        threads = []

        for page in range(last_page, last_page + page_batch_size):
            t = threading.Thread(target=append_cards_by_page, args=(api_key, content_id, language, statuses, page, results))
            threads.append(t)
            t.start()

        # completing process
        for t in threads:
            t.join()

        while not results.empty():
            result = results.get()

            if result.exception:
                print(str(result.exception))
                running = False
                has_error = True
                break

            if result.status == 200:
                cards.extend(result.cards)
            elif result.status == 404:
                running = False
            else:
                running = False
                has_error = True
                break

        last_page += 10

    return cards


def append_cards_by_page(api_key, content_id, language, statuses, page, results: Queue):

    cards_url = f"https://www.lingq.com/api/v2/{language}/cards?page={page}&page_size=200"

    if statuses:
        cards_url = cards_url + f"&status={statuses}"
    if content_id:
        cards_url = cards_url + f"&content_id={content_id}"

    result = CardPageResult(status=0, cards=[], exception=None)

    try:
        if statuses:
            cards_url = cards_url + f"&status={statuses}"

        if content_id:
            cards_url = cards_url + f"&content_id={content_id}"

        response = http.get(
            cards_url, headers={"Authorization": "Token {}".format(api_key)}
        )

        if response.status_code == 200:
            result.status = 200
            result.cards = response.json()["results"]

        if response.status_code == 404:
            result.status = 404
        else:
            result.status = response.status_code

    except Exception as e:
        result.exception = e

    results.put(result)


def validate_response(response):
    if response.status_code == 401:
        raise UnauthorizedException
    elif 199 >= response.status_code >= 400:
        raise UnexpectedResponseException
    
    return response


def get_active_languages(api_key):

    active_lang_url = "https://www.lingq.com/api/v2/contexts"

    response = validate_response(http.get(
        active_lang_url, headers={"Authorization": "Token {}".format(api_key)}
    ))

    languages = []
    for context in response.json()["results"]:
        languages.append(context["language"]["code"])

    return languages


def get_courses(api_key, language):
    url = f"https://www.lingq.com/api/v2/{language}/collections/my"

    response = validate_response(http.get(
        url, headers={"Authorization": "Token {}".format(api_key)}
    ))

    courses = []
    for context in response.json()["results"]:
        courses.append(context)

    return courses


def get_lessons(api_key, language, course_id):
    url = f"https://www.lingq.com/api/v3/{language}/collections/{course_id}/lessons"

    response = validate_response(http.get(
        url, headers={"Authorization": "Token {}".format(api_key)}
    ))

    courses = []
    for context in response.json()["results"]:
        courses.append(context)

    return courses


def batch(iterable, n=1):
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx:min(ndx + n, l)]