from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from core.util.sourcemod import auto_detect_sourcemod, validate_game_directory


class ProfileDialog(QDialog):
    def __init__(self, parent=None, name="", game_path="", game_target=""):
        super().__init__(parent)
        self.setWindowTitle("New Profile" if not name else "Edit Profile")
        self.setModal(True)

        self._name = name
        self._game_path = game_path
        self._game_target = game_target

        layout = QVBoxLayout(self)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        # Name
        layout.addWidget(QLabel("Profile Name:"))
        self.name_edit = QLineEdit()
        self.name_edit.setText(name)
        self.name_edit.setPlaceholderText("e.g. Main, Testing, Competitive...")
        self.name_edit.setMinimumWidth(400)
        layout.addWidget(self.name_edit)

        # Game target (Steam folder name)
        layout.addWidget(QLabel("Game Target (For auto detection, optional):"))
        self.game_target_edit = QLineEdit()
        self.game_target_edit.setText(game_target)
        self.game_target_edit.setPlaceholderText("e.g. Team Fortress 2, Team Fortress 2 Classified...")
        layout.addWidget(self.game_target_edit)

        # Game path
        layout.addWidget(QLabel("Game Directory:"))
        path_row = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        self.path_edit.setText(game_path)
        self.path_edit.setPlaceholderText("Select game directory containing gameinfo.txt...")
        path_row.addWidget(self.path_edit)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse)
        path_row.addWidget(browse_btn)
        layout.addLayout(path_row)

        auto_detect_btn = QPushButton("Auto-Detect")
        auto_detect_btn.clicked.connect(self.auto_detect)
        layout.addWidget(auto_detect_btn)

        self.validation_label = QLabel("")
        self.validation_label.setWordWrap(True)
        layout.addWidget(self.validation_label)

        if game_path:
            validate_game_directory(game_path, self.validation_label)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        ok_btn = QPushButton("Save")
        ok_btn.setProperty("primary", True)
        ok_btn.clicked.connect(self.try_accept)
        btn_row.addWidget(ok_btn)
        layout.addLayout(btn_row)

    def browse(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Game Directory")
        if directory:
            self._game_path = directory
            self.path_edit.setText(directory)
            validate_game_directory(directory, self.validation_label)

    def auto_detect(self):
        game_target = self.game_target_edit.text().strip() or "Team Fortress 2"
        path = auto_detect_sourcemod(game_target)
        if path:
            self._game_path = path
            self.path_edit.setText(path)
            validate_game_directory(path, self.validation_label)
            QMessageBox.information(self, "Auto-Detection Successful", f"Found {game_target} at:\n{path}")
        else:
            QMessageBox.information(self, "Auto-Detection Failed",
                                    f"Could not find '{game_target}' in common Steam locations.\n"
                                    "Please check the game target name or manually select your game directory.")

    def try_accept(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Please enter a profile name.")
            return
        if not self._game_path:
            QMessageBox.warning(self, "Validation Error", "Please select a game directory.")
            return
        self._name = name
        self._game_target = self.game_target_edit.text().strip() or "Team Fortress 2"
        self.accept()

    def get_name(self):
        return self._name

    def get_game_path(self):
        return self._game_path

    def get_game_target(self):
        return self._game_target
