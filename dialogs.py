"""
Daily Schedule Reminder — Dialogs
Add/Edit item dialog and Settings dialog
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTimeEdit, QCheckBox, QPushButton, QWidget, QFormLayout,
    QMessageBox,
)
from PyQt6.QtCore import QTime, Qt

from theme import (
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_TERTIARY, BG_SURFACE, BG_SECONDARY,
    BRAND_ACCENT, BRAND_GREEN, BORDER_STANDARD, BORDER_SUBTLE, BORDER_SOLID,
    FONT_SIZE_SM, FONT_SIZE_MD, STYLE_INPUT, STYLE_CHECKBOX,
)

import database
import telegram_notifier


class ScheduleItemDialog(QDialog):
    """Dialog for adding or editing a schedule item."""

    def __init__(self, parent=None, item: dict = None):
        super().__init__(parent)
        self.item = item  # None for add, dict for edit
        self.setWindowTitle("Добавить задачу" if not item else "Редактировать задачу")
        self.setMinimumWidth(400)
        self.setup_ui()

        if item:
            self.load_item(item)

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Time
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Время:"))
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setTime(QTime.currentTime())
        time_layout.addWidget(self.time_edit)
        layout.addLayout(time_layout)

        # Text
        text_layout = QHBoxLayout()
        text_layout.addWidget(QLabel("Задача:"))
        self.text_edit = QLineEdit()
        self.text_edit.setPlaceholderText("Что нужно сделать?")
        text_layout.addWidget(self.text_edit)
        layout.addLayout(text_layout)

        # Days
        layout.addWidget(QLabel("Дни недели:"))
        days_layout = QHBoxLayout()
        self.day_checkboxes = []
        day_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        for i, name in enumerate(day_names):
            cb = QCheckBox(name)
            cb.setChecked(True)
            self.day_checkboxes.append(cb)
            days_layout.addWidget(cb)
        layout.addLayout(days_layout)

        # Enabled
        self.enabled_cb = QCheckBox("Активно")
        self.enabled_cb.setChecked(True)
        layout.addWidget(self.enabled_cb)

        # Buttons
        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("✅ Сохранить")
        self.ok_btn.setStyleSheet("""
            QPushButton { background-color: #5E6AD2; color: white; border: none;
            border-radius: 6px; padding: 8px 20px; font-size: 13px; font-weight: 500; }
            QPushButton:hover { background-color: #828FFF; }
        """)
        self.ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.setStyleSheet("""
            QPushButton { background-color: rgba(255,255,255,0.05); color: #D0D6E0;
            border: 1px solid rgba(255,255,255,0.08); border-radius: 6px; padding: 8px 20px; font-size: 13px; }
            QPushButton:hover { background-color: rgba(255,255,255,0.1); }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def load_item(self, item: dict):
        self.time_edit.setTime(QTime.fromString(item["time"], "HH:mm"))
        self.text_edit.setText(item["text"])
        self.enabled_cb.setChecked(bool(item["enabled"]))
        mask = item["days_mask"]
        for i, cb in enumerate(self.day_checkboxes):
            cb.setChecked(bool(mask & (1 << i)))

    def get_data(self) -> dict:
        mask = 0
        for i, cb in enumerate(self.day_checkboxes):
            if cb.isChecked():
                mask |= 1 << i
        return {
            "time": self.time_edit.time().toString("HH:mm"),
            "text": self.text_edit.text().strip(),
            "days_mask": mask,
            "enabled": self.enabled_cb.isChecked(),
        }


class SettingsDialog(QDialog):
    """Dialog for Telegram settings."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки Telegram")
        self.setMinimumWidth(450)
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.token_edit = QLineEdit()
        self.token_edit.setPlaceholderText("123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")
        self.token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Bot Token:", self.token_edit)

        self.chat_id_edit = QLineEdit()
        self.chat_id_edit.setPlaceholderText("123456789")
        form.addRow("Chat ID:", self.chat_id_edit)

        layout.addLayout(form)

        # Notifications options
        notif_group = QGroupBox("🔊 Озвучивание")
        notif_group.setStyleSheet(f"""
            QGroupBox {{ color: {TEXT_SECONDARY}; font-size: 13px; font-weight: 500;
            border: 1px solid {BORDER_STANDARD}; border-radius: 8px; margin-top: 8px; padding: 12px; }}
            QGroupBox::title {{ color: {TEXT_SECONDARY}; }}
        """)
        notif_layout = QVBoxLayout(notif_group)
        self.notify_pc_cb = QCheckBox("Показывать уведомления на ПК")
        self.notify_pc_cb.setChecked(True)
        notif_layout.addWidget(self.notify_pc_cb)
        self.notify_voice_cb = QCheckBox("🎤 Озвучивать напоминания голосом на ПК")
        self.notify_voice_cb.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 13px; spacing: 8px;")
        notif_layout.addWidget(self.notify_voice_cb)
        self.notify_tg_cb = QCheckBox("📱 Отправлять в Telegram")
        notif_layout.addWidget(self.notify_tg_cb)
        self.voice_tg_cb = QCheckBox("🎤 Отправлять голосовые сообщения в Telegram вместо текста")
        self.voice_tg_cb.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 13px; spacing: 8px;")
        notif_layout.addWidget(self.voice_tg_cb)
        layout.addWidget(notif_group)

        # Test button
        test_btn = QPushButton("📨 Тест Telegram")
        test_btn.setStyleSheet("""
            QPushButton { background-color: rgba(16, 185, 129, 0.1); color: #10B981;
            border: 1px solid rgba(16, 185, 129, 0.2); border-radius: 6px; padding: 8px 16px; font-size: 13px; }
            QPushButton:hover { background-color: rgba(16, 185, 129, 0.2); }
        """)
        test_btn.clicked.connect(self.test_telegram)
        layout.addWidget(test_btn)

        # Save / Cancel
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Сохранить")
        save_btn.setStyleSheet("""
            QPushButton { background-color: #5E6AD2; color: white; border: none;
            border-radius: 6px; padding: 8px 20px; font-size: 13px; font-weight: 500; }
            QPushButton:hover { background-color: #828FFF; }
        """)
        save_btn.clicked.connect(self.save_settings)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.setStyleSheet("""
            QPushButton { background-color: rgba(255,255,255,0.05); color: #D0D6E0;
            border: 1px solid rgba(255,255,255,0.08); border-radius: 6px; padding: 8px 20px; font-size: 13px; }
            QPushButton:hover { background-color: rgba(255,255,255,0.1); }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def load_settings(self):
        self.token_edit.setText(database.get_setting("telegram_token"))
        self.chat_id_edit.setText(database.get_setting("telegram_chat_id"))
        self.notify_pc_cb.setChecked(database.get_setting("notify_pc") == "1")
        self.notify_voice_cb.setChecked(database.get_setting("notify_voice") == "1")
        self.notify_tg_cb.setChecked(database.get_setting("notify_telegram") == "1")
        self.voice_tg_cb.setChecked(database.get_setting("voice_telegram") == "1")

    def save_settings(self):
        database.set_setting("telegram_token", self.token_edit.text().strip())
        database.set_setting("telegram_chat_id", self.chat_id_edit.text().strip())
        database.set_setting("notify_pc", "1" if self.notify_pc_cb.isChecked() else "0")
        database.set_setting("notify_voice", "1" if self.notify_voice_cb.isChecked() else "0")
        database.set_setting("notify_telegram", "1" if self.notify_tg_cb.isChecked() else "0")
        database.set_setting("voice_telegram", "1" if self.voice_tg_cb.isChecked() else "0")
        QMessageBox.information(self, "Готово", "Настройки сохранены!")
        self.accept()

    def test_telegram(self):
        token = self.token_edit.text().strip()
        chat_id = self.chat_id_edit.text().strip()
        if not token or not chat_id:
            QMessageBox.warning(self, "Ошибка", "Введите Token и Chat ID")
            return

        success, msg = telegram_notifier.test_connection(token, chat_id)
        if success:
            QMessageBox.information(self, "Успех", msg)
        else:
            QMessageBox.critical(self, "Ошибка", msg)
