from dataclasses import dataclass, field
from collections import defaultdict

import aqt
from anki.utils import ids2str, splitFields
from aqt import mw, QAction, qconnect
from aqt.operations import QueryOp
from aqt.utils import showInfo

from .config_dialog import show_config_dialog
from .lingq import get_all_cards, VocabRetrieveResult, UnauthorizedException, UnexpectedResponseException
from .model import get_model

_deck_name = "LingQ Sync Deck"
WORD_CHUNK_SIZE = 50
ADD_STATUS_TEMPLATE = "Importing from LingQ: {} of {} complete."


@dataclass
class AddVocabResult:
    notes_added: int = 0


def on_retrieve_success(retrieve_result: VocabRetrieveResult):
    if retrieve_result.success is False:
        return

    model = get_model(mw)

    note_ids = mw.col.findNotes('tag:lingq_sync')
    notes = mw.col.db.list("select flds from notes where id in {}".format(ids2str(note_ids)))
    gids_to_notes = {splitFields(note)[0]: note for note in notes}

    did = mw.col.decks.id(_deck_name)
    mw.col.decks.select(did)

    deck = mw.col.decks.get(did)
    deck['mid'] = model['id']
    mw.col.decks.save(deck)

    aqt.mw.taskman.run_on_main(
        lambda: mw.progress.update(label="LingQs downloaded, syncing notes..")
    )

    retrieve_result.cards = [card for card in retrieve_result.cards if str(card['pk']) not in gids_to_notes]

    add_vocab(retrieve_result, did)

    aqt.mw.taskman.run_on_main(
        lambda: mw.progress.finish()
    )

    mw.moveToState("deckBrowser")


def get_lessons(card_id, courses):
    results = []

    for course in courses:
        for lesson in course['lessons']:
            if str(card_id) in lesson['card_ids']:
                results.append(lesson)

    return results


def clean_tag(input):
    return input.replace(" ", "_").replace("-", "").replace("(", "").replace(")", "")


def add_vocab(retrieve_result: VocabRetrieveResult, did) -> AddVocabResult:
    result = AddVocabResult()

    total_card_count = len(retrieve_result.cards)
    card_chunks = [retrieve_result.cards[x:x + WORD_CHUNK_SIZE] for x in
                   range(0, total_card_count, WORD_CHUNK_SIZE)]

    aqt.mw.taskman.run_on_main(
        lambda: mw.progress.update(label=ADD_STATUS_TEMPLATE.format(0, total_card_count), value=0, max=total_card_count)
    )

    cards_processed = 0
    for card_chunk in card_chunks:

        for card in card_chunk:
            n = mw.col.newNote()

            # Update the underlying dictionary to accept more arguments for more customisable cards
            n._fmap = defaultdict(str, n._fmap)

            n['Pk'] = str(card['pk'])
            n['Term'] = card['term']
            n['Fragment'] = card['fragment']

            if card['hints']:
                n['Hint'] = ';'.join([hint["text"] for hint in card["hints"]])
            else:
                n['Hint'] = ""

            n.tags.append('lingq_sync')

            lessons = get_lessons(card['pk'], retrieve_result.courses)

            for lesson in lessons:
                tag_title = "lingq_courses::" + clean_tag(lesson["collectionTitle"]) + "::" + clean_tag(lesson["title"])
                n.tags.append(tag_title)

            n['gTags'] = ' '.join([clean_tag(tag) for tag in card["gTags"]])

            # if card['pos']:
            #     n.addTag(card['pos'])

            mw.col.add_note(n, did)
            cards_processed += 1

            aqt.mw.taskman.run_on_main(
                lambda: mw.progress.update(label=ADD_STATUS_TEMPLATE.format(result.notes_added, total_card_count),
                                           value=cards_processed, max=total_card_count)
            )


    return result


def retrieve_vocab(api_key) -> VocabRetrieveResult:
    try:
        result = get_all_cards(api_key)

        return result
    except UnauthorizedException:
        aqt.mw.taskman.run_on_main(
            lambda: mw.progress.finish()
        )
        aqt.mw.taskman.run_on_main(
            lambda: showInfo("LingQ return unauthorized. Make sure your API key is setup in the config dialog.")
        )
    except UnexpectedResponseException:
        aqt.mw.taskman.run_on_main(
            lambda: mw.progress.finish()
        )
        aqt.mw.taskman.run_on_main(
            lambda: showInfo("LingQ returned unexpected response.")
        )
    except Exception as e:
        aqt.mw.taskman.run_on_main(
            lambda: mw.progress.finish()
        )
        aqt.mw.taskman.run_on_main(
            lambda: showInfo("Unexpected exception downloading vocabulary: " + e)
        )

    return VocabRetrieveResult(success=False)


def sync_lingq():
    config = mw.addonManager.getConfig(__name__)
    api_key = config["api_key"]

    op = QueryOp(
        parent=mw,
        op=lambda col: retrieve_vocab(api_key),
        success=on_retrieve_success,
    )

    op.with_progress(label="Syncing...").run_in_background()


mw.addonManager.setConfigAction(__name__, show_config_dialog)

print(mw.addonManager.getConfig(__name__))

# create a new menu item, "test"
sync_action = QAction("Sync LingQ", mw)
# set it to call testFunction when it's clicked
qconnect(sync_action.triggered, sync_lingq)

mw.form.menuTools.addAction(sync_action)
