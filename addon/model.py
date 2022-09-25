from aqt.utils import showInfo

_field_names = ["Pk", "Term", "Fragment", "Hint", "gTags", "Language"]
_model_name = "LingQ Sync"


def create_model(mw, include_reverse):
    config = mw.addonManager.getConfig(__name__)

    mm = mw.col.models
    m = mm.new(_model_name)

    for field_name in _field_names:
        fm = mm.newField(field_name)
        mm.addField(m, fm)

    t = mm.newTemplate("LingQ Basic")
    t['qfmt'] = "{{Term}}<br><br><hr id=answer>"
    t['afmt'] = "{{FrontSide}}\n\n<br>{{Hint}}<br><br>\n\n<i><small>{{Fragment}}</small></i>"
    mm.addTemplate(m, t)

    if include_reverse:
        t = mm.newTemplate("LingQ Reverse")
        t['qfmt'] = "{{Hint}}<br><br><hr id=answer>"
        t['afmt'] = "{{FrontSide}}\n\n<br><br>{{Term}}<br><br>\n\n<i><small>{{Fragment}}</small></i>"
        mm.addTemplate(m, t)

    mm.add(m)
    mw.col.models.save(m)
    return m


def get_model(mw):
    config = mw.addonManager.getConfig(__name__)
    include_reverse = config["include_reverse_card"]

    m = mw.col.models.byName(_model_name)

    if not m:
        showInfo("LingQ Sync note type not found. Creating.")
        m = create_model(mw, include_reverse)

    # Add new fields if they don't exist yet
    fields_to_add = [field_name for field_name in _field_names if field_name not in mw.col.models.field_names(m)]
    if fields_to_add:
        showInfo("""
        <p>The LingQ Sync plugin has recently been upgraded to include the following attributes: {}</p>
        <p>This change will require a full-sync of your card database to your Anki-Web account.</p>
        """.format(", ".join(fields_to_add)))
        for field_name in fields_to_add:
            pass
            fm = mw.col.models.newField(field_name)
            mw.col.models.addField(m, fm)
            mw.col.models.save(m)

    return m
