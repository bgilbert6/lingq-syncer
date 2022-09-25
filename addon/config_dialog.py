from aqt.qt import *
from aqt import mw


def show_config_dialog():
    config = mw.addonManager.getConfig(__name__)

    print(config)

    # Create a dialog window
    dialog = QDialog(mw)
    # Set window title
    dialog.setWindowTitle("LingQ Syncer Settings")
    # Set window type to modal
    dialog.setWindowModality(Qt.WindowModal)

    # Create a VBox layout - Each new widget is added vertically
    vbox = QVBoxLayout()
    vbox.setContentsMargins(30, 30, 30, 30)

    # Create modal text
    modal_text = QLabel(
        """
        <p>Please enter your LingQ API key. 
        <a href="https://www.lingq.com/en/accounts/apikey/" 
        target="_blank">Click here to get 
        API key</a></p> 
        """
    )

    # Allow links to be open in browser from modal text
    modal_text.setOpenExternalLinks(True)
    # Configure modal text properties
    modal_text.setWordWrap(True)
    # Add modal text to vertical layout
    vbox.addWidget(modal_text)

    # Add some empty space before next item
    vbox.addSpacing(20)

    grid_layout = QGridLayout()

    api_key_label = QLabel("LingQ Api Key:")
    grid_layout.addWidget(api_key_label, 0, 0)

    api_key_input = QLineEdit()
    api_key_input.setText(config["api_key"])
    grid_layout.addWidget(api_key_input, 0, 1)

    grid_layout.addWidget(QLabel("Statuses:"), 1, 0)
    statuses_input = QLineEdit()
    statuses_input.setText(config["included_statuses"])
    grid_layout.addWidget(statuses_input, 1, 1)

    grid_layout.addWidget(QLabel("Include Reverse Card:"), 2, 0)
    reverse_card_input = QCheckBox()
    reverse_card_input.setChecked(config["include_reverse_card"])
    grid_layout.addWidget(reverse_card_input, 2, 1)

    grid_layout.addWidget(QLabel("Include Lesson Tags:"), 3, 0)
    include_lesson_tags_input = QCheckBox()
    include_lesson_tags_input.setChecked(config["include_lesson_tags"])
    grid_layout.addWidget(include_lesson_tags_input, 3, 1)

    # Add user details grid to vertical layout
    vbox.addLayout(grid_layout)

    # Add confirmation button
    bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    bb.button(QDialogButtonBox.Ok).setAutoDefault(True)
    bb.accepted.connect(dialog.accept)
    bb.rejected.connect(dialog.reject)
    vbox.addWidget(bb)

    dialog.setLayout(vbox)
    dialog.show()

    # Resume execution after confirmation pressed
    accepted = dialog.exec_()

    if accepted:
        config["api_key"] = api_key_input.text()
        config["included_statuses"] = statuses_input.text()
        config["include_reverse_card"] = reverse_card_input.isChecked()
        config["include_lesson_tags"] = include_lesson_tags_input.isChecked()

        mw.addonManager.writeConfig(__name__, config)

    return
