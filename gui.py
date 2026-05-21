"""
Daily Schedule Reminder — Main GUI Window
+ Goals tab integration
"""

import sys
import logging
import threading
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QCheckBox, QLabel, QMessageBox, QSystemTrayIcon, QMenu,
    QTabWidget, QGroupBox, QGridLayout, QProgressBar, QTextEdit,
    QFrame,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QIcon, QFont, QColor

import database
from dialogs import ScheduleItemDialog, SettingsDialog
from reminder_engine import ReminderEngine
from goals import load_all_goals, get_today_schedule, get_urgent_tasks

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

DAY_NAMES = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

GOAL_COLORS = {
    1: "#4A90D9",  # Finance - blue
    2: "#7B68EE",  # Intellect - purple
    3: "#FF6B6B",  # Creative - red
    4: "#51CF66",  # Body - green
    5: "#FFA94D",  # Business - orange
    6: "#FF6B9D",  # Networking - pink
}


class GoalsWidget(QWidget):
    """Widget displaying goals, subtasks, and today's schedule."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Top: total progress
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(QLabel("Общий прогресс:"))
        self.total_progress_bar = QProgressBar()
        self.total_progress_bar.setRange(0, 100)
        self.total_progress_bar.setTextVisible(True)
        progress_layout.addWidget(self.total_progress_bar)
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setToolTip("Обновить")
        self.refresh_btn.setFixedWidth(40)
        self.refresh_btn.clicked.connect(self.load_data)
        progress_layout.addWidget(self.refresh_btn)
        layout.addLayout(progress_layout)

        # Today's schedule
        today_group = QGroupBox("🗓️ Расписание на сегодня")
        today_layout = QVBoxLayout(today_group)
        self.today_text = QTextEdit()
        self.today_text.setReadOnly(True)
        self.today_text.setMaximumHeight(120)
        today_layout.addWidget(self.today_text)
        layout.addWidget(today_group)

        # Urgent tasks
        urgent_group = QGroupBox("🔥 Срочные задачи")
        urgent_layout = QVBoxLayout(urgent_group)
        self.urgent_text = QTextEdit()
        self.urgent_text.setReadOnly(True)
        self.urgent_text.setMaximumHeight(100)
        urgent_layout.addWidget(self.urgent_text)
        layout.addWidget(urgent_group)

        # Goals progress bars
        goals_group = QGroupBox("🎯 Генеральные цели")
        goals_layout = QVBoxLayout(goals_group)
        self.goal_bars = []  # (label, progress_bar)
        for i in range(6):
            bar_layout = QHBoxLayout()
            label = QLabel("")
            label.setFixedWidth(250)
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setTextVisible(True)
            bar_layout.addWidget(label)
            bar_layout.addWidget(bar)
            goals_layout.addLayout(bar_layout)
            self.goal_bars.append((label, bar))
        layout.addWidget(goals_group)

        # Subtasks table (compact)
        subtasks_group = QGroupBox("📋 Подзадачи")
        subtasks_layout = QVBoxLayout(subtasks_group)
        self.subtask_table = QTableWidget()
        self.subtask_table.setColumnCount(5)
        self.subtask_table.setHorizontalHeaderLabels(["Цель", "Задача", "Дедлайн", "Прогресс", "Статус"])
        self.subtask_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.subtask_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.subtask_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.subtask_table.verticalHeader().setVisible(False)
        subtasks_layout.addWidget(self.subtask_table)
        layout.addWidget(subtasks_group)

    def load_data(self):
        try:
            data = load_all_goals()
        except Exception as e:
            self.today_text.setText(f"⚠️ Файл целей не найден: {e}")
            return

        # Total progress
        prog = data.get("total_progress", 0)
        self.total_progress_bar.setValue(int(prog))
        self.total_progress_bar.setFormat(f"{prog}%")

        # Today schedule
        today_info = get_today_schedule()
        if today_info:
            text = f"📅 {today_info.get('date', '').strftime('%d.%m.%Y') if hasattr(today_info.get('date'), 'strftime') else ''}"
            text += f"  |  🔥 {today_info.get('priority', '')}"
            text += f"\n🌅 {today_info.get('morning', '')}"
            text += f"\n💼 {today_info.get('work_morning', '')} / {today_info.get('work_evening', '')}"
            text += f"\n📚 {today_info.get('development', '')}"
            self.today_text.setText(text)
        else:
            self.today_text.setText("Расписание на сегодня не найдено")

        # Urgent tasks
        urgent = get_urgent_tasks()
        if urgent:
            text = ""
            for t in urgent[:5]:
                days = t.get("days_left", 0)
                emoji = "🔥" if days <= 0 else "⏰"
                text += f"{emoji} {t['name']} — {t.get('deadline', '')} ({'просрочено' if days < 0 else f'осталось {days} дн.'})\n"
            self.urgent_text.setText(text)
        else:
            self.urgent_text.setText("✅ Срочных задач нет")

        # Goal progress bars
        color_values = ["#4A90D9", "#7B68EE", "#FF6B6B", "#51CF66", "#FFA94D", "#FF6B9D"]
        for i, (label, bar) in enumerate(self.goal_bars):
            if i < len(data.get("goals", [])):
                goal = data["goals"][i]
                pct = goal.get("progress", 0)
                if isinstance(pct, str):
                    try:
                        pct = float(pct)
                    except:
                        pct = 0
                label.setText(f"{goal['name']}")
                bar.setValue(int(pct))
                bar.setFormat(f"{int(pct)}%")
                # Set color via stylesheet
                color = color_values[i] if i < len(color_values) else "#888"
                bar.setStyleSheet(f"""
                    QProgressBar {{ border: 1px solid #555; border-radius: 4px; text-align: center; height: 22px; }}
                    QProgressBar::chunk {{ background-color: {color}; border-radius: 3px; }}
                """)

        # Subtasks table
        subtasks = data.get("subtasks", [])
        self.subtask_table.setRowCount(len(subtasks))
        for row, task in enumerate(subtasks):
            goal_name = ""
            for g in data.get("goals", []):
                if g["id"] == task["goal_id"]:
                    goal_name = g["name"][:20]
                    break
            self.subtask_table.setItem(row, 0, QTableWidgetItem(goal_name))
            self.subtask_table.setItem(row, 1, QTableWidgetItem(task["name"]))
            self.subtask_table.setItem(row, 2, QTableWidgetItem(task.get("deadline", "")))
            prog = task.get("progress", 0)
            self.subtask_table.setItem(row, 3, QTableWidgetItem(f"{int(prog) if prog else 0}%"))
            status = task.get("status", "")
            item = QTableWidgetItem(status)
            if status in ("Горит", "Просрочено", "Срочно"):
                item.setForeground(QColor("#FF4444"))
            elif status == "Выполнено":
                item.setForeground(QColor("#44CC44"))
            self.subtask_table.setItem(row, 4, item)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Assistent denisa")
        self.setMinimumSize(800, 600)

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

        # Auto-refresh goals every 5 minutes
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_goals)
        self.refresh_timer.start(300000)  # 5 min

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setFont(QFont("Segoe UI", 10))

        # Tab 1: Schedule (original)
        schedule_tab = QWidget()
        schedule_layout = QVBoxLayout(schedule_tab)
        self.setup_schedule_tab(schedule_layout)
        self.tabs.addTab(schedule_tab, "⏰ Расписание")

        # Tab 2: Goals
        self.goals_widget = GoalsWidget()
        self.tabs.addTab(self.goals_widget, "🎯 Цели 2026")

        layout.addWidget(self.tabs)

    def setup_schedule_tab(self, layout):
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
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setToolTip("Assistent denisa")

        icon = self.style().standardIcon(
            self.style().StandardPixmap.SP_ComputerIcon
        )
        self.tray_icon.setIcon(icon)

        tray_menu = QMenu()
        show_action = QAction("Показать", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)

        goals_action = QAction("🎯 Цели 2026", self)
        goals_action.triggered.connect(lambda: self.show_and_tab(1))
        tray_menu.addAction(goals_action)

        settings_action = QAction("Настройки", self)
        settings_action.triggered.connect(self.open_settings)
        tray_menu.addAction(settings_action)

        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.quit_app)
        tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        self.tray_icon.activated.connect(self.tray_clicked)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)

    def show_and_tab(self, tab_index):
        self.show()
        self.tabs.setCurrentIndex(tab_index)

    def tray_clicked(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show()

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "Assistent denisa",
            "Программа свёрнута в трей. Напоминания продолжают работать.",
            QSystemTrayIcon.MessageIcon.Information,
            3000,
        )

    def quit_app(self):
        self.engine.stop()
        self.engine.wait(2000)
        QApplication.quit()

    def refresh_goals(self):
        self.goals_widget.load_data()

    def refresh_table(self):
        items = database.get_all_items()
        self.table.setRowCount(len(items))

        for row, item in enumerate(items):
            self.table.setItem(row, 0, QTableWidgetItem(item["time"]))
            self.table.setItem(row, 1, QTableWidgetItem(item["text"]))
            mask = item["days_mask"]
            days_str = ", ".join(
                DAY_NAMES[i] for i in range(7) if mask & (1 << i)
            )
            self.table.setItem(row, 2, QTableWidgetItem(days_str))

            enabled_item = QTableWidgetItem()
            enabled_item.setFlags(enabled_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            enabled_item.setCheckState(
                Qt.CheckState.Checked if item["enabled"] else Qt.CheckState.Unchecked
            )
            enabled_item.setData(Qt.ItemDataRole.UserRole, item["id"])
            self.table.setItem(row, 3, enabled_item)

        self.table.itemChanged.connect(self.on_enabled_changed)
        self.table.verticalHeader().setVisible(False)

    def on_enabled_changed(self, item):
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
        notify_pc = database.get_setting("notify_pc") == "1"
        if notify_pc:
            try:
                from plyer import notification
                notification.notify(
                    title=title,
                    message=message,
                    app_name="Assistent denisa",
                    timeout=10,
                )
            except Exception as e:
                logger.warning(f"PC notification failed: {e}")

        if self.tray_icon:
            self.tray_icon.showMessage(
                title, message,
                QSystemTrayIcon.MessageIcon.Information, 10000
            )


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Assistent denisa")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
