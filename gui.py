"""
Daily Schedule Reminder — Main GUI Window
"""

import sys
import logging

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QCheckBox, QLabel, QMessageBox, QSystemTrayIcon, QMenu,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QIcon

import database
from dialogs import ScheduleItemDialog, SettingsDialog
from reminder_engine import ReminderEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

DAY_NAMES = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Daily Schedule Reminder")
        self.setMinimumSize(700, 500)

        # Init DB
        database.init_db()

        # Setup UI
        self.setup_ui()

        # Start reminder engine
        self.engine = ReminderEngine()
        self.engine.notification_signal.connect(self.show_notification)
        self.engine.start()

        # Setup system tray
        self.setup_tray()

        # Load data
        self.refresh_table()

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Top: settings button
        top_layout = QHBoxLayout()
        settings_btn = QPushButton("⚙️ Настройки Telegram")
        settings_btn.clicked.connect(self.open_settings)
        top_layout.addWidget(settings_btn)
        top_layout.addStretch()
        layout.addLayout(top_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Время", "Задача", "Дни", "Активно"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        # Bottom buttons
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("➕ Добавить")
        add_btn.clicked.connect(self.add_item)
        edit_btn = QPushButton("✏️ Редактировать")
        edit_btn.clicked.connect(self.edit_item)
        delete_btn = QPushButton("🗑️ Удалить")
        delete_btn.clicked.connect(self.delete_item)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(delete_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def setup_tray(self):
        """Setup system tray icon with context menu."""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setToolTip("Daily Schedule Reminder")

        # Use a default icon
        icon = self.style().standardIcon(
            self.style().StandardPixmap.SP_ComputerIcon
        )
        self.tray_icon.setIcon(icon)

        # Tray menu
        tray_menu = QMenu()
        show_action = QAction("Показать", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)

        settings_action = QAction("Настройки", self)
        settings_action.triggered.connect(self.open_settings)
        tray_menu.addAction(settings_action)

        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.quit_app)
        tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        # Minimize to tray on close
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)

    def closeEvent(self, event):
        """Minimize to tray instead of closing."""
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "Daily Schedule Reminder",
            "Программа свёрнута в трей. Напоминания продолжают работать.",
            QSystemTrayIcon.MessageIcon.Information,
            3000,
        )

    def quit_app(self):
        """Actually quit the application."""
        self.engine.stop()
        self.engine.wait(2000)
        QApplication.quit()

    def refresh_table(self):
        """Reload table data from database."""
        items = database.get_all_items()
        self.table.setRowCount(len(items))

        for row, item in enumerate(items):
            # Time
            self.table.setItem(row, 0, QTableWidgetItem(item["time"]))

            # Text
            self.table.setItem(row, 1, QTableWidgetItem(item["text"]))

            # Days
            mask = item["days_mask"]
            days_str = ", ".join(
                DAY_NAMES[i] for i in range(7) if mask & (1 << i)
            )
            self.table.setItem(row, 2, QTableWidgetItem(days_str))

            # Enabled
            enabled_item = QTableWidgetItem()
            enabled_item.setFlags(enabled_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            enabled_item.setCheckState(
                Qt.CheckState.Checked if item["enabled"] else Qt.CheckState.Unchecked
            )
            enabled_item.setData(Qt.ItemDataRole.UserRole, item["id"])
            self.table.setItem(row, 3, enabled_item)

            # Connect enabled checkbox change
            self.table.itemChanged.connect(self.on_enabled_changed)

        # Hide row numbers
        self.table.verticalHeader().setVisible(False)

    def on_enabled_changed(self, item):
        """Handle enabled checkbox toggle."""
        if item.column() == 3:
            item_id = item.data(Qt.ItemDataRole.UserRole)
            if item_id is not None:
                enabled = item.checkState() == Qt.CheckState.Checked
                database.update_item(item_id, enabled=enabled)

    def add_item(self):
        dialog = ScheduleItemDialog(self)
        if dialog.exec() == ScheduleItemDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if data["text"]:
                database.add_item(
                    data["time"], data["text"],
                    data["days_mask"], data["enabled"],
                )
                self.refresh_table()
            else:
                QMessageBox.warning(self, "Ошибка", "Введите текст задачи")

    def edit_item(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите задачу для редактирования")
            return

        items = database.get_all_items()
        if row >= len(items):
            return

        item = items[row]
        dialog = ScheduleItemDialog(self, item=item)
        if dialog.exec() == ScheduleItemDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if data["text"]:
                database.update_item(
                    item["id"],
                    time=data["time"],
                    text=data["text"],
                    days_mask=data["days_mask"],
                    enabled=data["enabled"],
                )
                self.refresh_table()

    def delete_item(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите задачу для удаления")
            return

        items = database.get_all_items()
        if row >= len(items):
            return

        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Удалить задачу '{items[row]['text']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            database.delete_item(items[row]["id"])
            self.refresh_table()

    def open_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec()

    def show_notification(self, title: str, message: str):
        """Show PC notification."""
        notify_pc = database.get_setting("notify_pc") == "1"
        if not notify_pc:
            return

        try:
            from plyer import notification
            notification.notify(
                title=title,
                message=message,
                app_name="Daily Schedule",
                timeout=10,
            )
        except Exception as e:
            logger.warning(f"PC notification failed: {e}")

        # Also show tray notification
        if self.tray_icon:
            self.tray_icon.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 10000)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Daily Schedule Reminder")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
