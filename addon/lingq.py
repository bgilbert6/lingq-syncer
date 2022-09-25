import threading
from dataclasses import dataclass, field

import aqt
import requests as http
from aqt import mw
from aqt.utils import showInfo


@dataclass
class VocabRetrieveResult:
    success: bool = False
    cards: list = field(default_factory=list)
    courses: list = field(default_factory=list)


class UnauthorizedException(Exception):
    pass


class UnexpectedResponseException(Exception):
    pass


def get_all_cards(api_key):
    languages = get_active_languages(api_key)
    config = mw.addonManager.getConfig(__name__)
    statuses = config["included_statuses"]

    result = VocabRetrieveResult(success=True, cards=[], courses=[])

    for language in languages:
        result.cards = get_cards(api_key, "", language, statuses)

        if config["include_lesson_tags"] is True:

            courses = get_courses(api_key, language)

            for course in courses:

                lessons = get_lessons(api_key, language, course["pk"])
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

    cards_url = f"https://www.lingq.com/api/v2/{language}/cards?page_size=200"

    if statuses:
        cards_url = cards_url + f"&status={statuses}"

    if content_id:
        cards_url = cards_url + f"&content_id={content_id}"

    response = validate_response(http.get(
        cards_url, headers={"Authorization": "Token {}".format(api_key)}
    )).json()

    cards = []

    # Iterate over paginated response until all cards collected
    while True:
        # collect page of cards
        cards.extend(response["results"])

        #response["next"] = ""

        if not response["next"]:
            break

        cards_url = response["next"]
        # get next page of cards
        response = validate_response(http.get(
            cards_url, headers={"Authorization": "Token {}".format(api_key)}
        )).json()

    return cards


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

