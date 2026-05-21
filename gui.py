"""
Daily Schedule Reminder — Main GUI Window
+ Goals tab + completion tracking + stats
"""

import sys
import logging
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QCheckBox, QLabel, QMessageBox, QSystemTrayIcon, QMenu,
    QTabWidget, QGroupBox, QProgressBar, QTextEdit,
    QFrame,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QFont, QColor

import database
from dialogs import ScheduleItemDialog, SettingsDialog
from reminder_engine import ReminderEngine
from goals import load_all_goals, get_today_schedule, get_urgent_tasks
from sync_goals import auto_sync
from focus_timer import FocusTimer, FocusMode
from productivity_analytics import analyze_performance, get_motivation, get_ai_recommendation, get_day_status
from theme import TEXT_PRIMARY, TEXT_SECONDARY, TEXT_TERTIARY, TEXT_QUATERNARY
from theme import BG_PRIMARY, BG_PANEL, BG_SURFACE, BG_SECONDARY
from theme import BRAND_ACCENT, BRAND_GREEN, BRAND_RED, BRAND_ORANGE
from theme import BORDER_SUBTLE, BORDER_STANDARD, BORDER_SOLID
from theme import FONT_SIZE_SM, FONT_SIZE_MD, FONT_SIZE_LG, FONT_SIZE_XL
from theme import SPACING_SM, SPACING_MD, SPACING_LG, SPACING_XL
from neon_theme import TEXT_NEON_CYAN, TEXT_NEON_WHITE, TEXT_MUTED, FONT_MONO

# Голосовые модули
from live_avatar import AnimatedAvatarWidget
from voice_assistant import speak, _init_player
from voice_commands import parse_command
from command_actions import process_command
from stt_engine import (
    transcribe_with_whisper, transcribe_with_google,
    record_from_mic, WHISPER_AVAILABLE, SR_AVAILABLE
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

DAY_NAMES = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

GOAL_COLORS = {
    1: "#4A90D9", 2: "#7B68EE", 3: "#FF6B6B",
    4: "#51CF66", 5: "#FFA94D", 6: "#FF6B9D",
}


class StatsWidget(QWidget):
    """Statistics and dynamics tab."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.refresh()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Today stats
        today_group = QGroupBox("📊 Сегодня")
        today_layout = QHBoxLayout(today_group)
        self.today_done_label = QLabel("Выполнено: 0")
        self.today_done_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #51CF66;")
        self.today_total_label = QLabel("Всего: 0")
        self.today_total_label.setStyleSheet("font-size: 18px;")
        self.today_pct_label = QLabel("0%")
        self.today_pct_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #4A90D9;")
        today_layout.addWidget(self.today_done_label)
        today_layout.addWidget(self.today_total_label)
        today_layout.addStretch()
        today_layout.addWidget(self.today_pct_label)
        layout.addWidget(today_group)

        # Week stats
        week_group = QGroupBox("📅 Неделя")
        week_layout = QVBoxLayout(week_group)
        self.week_table = QTableWidget()
        self.week_table.setColumnCount(3)
        self.week_table.setHorizontalHeaderLabels(["День", "Выполнено", "Всего"])
        self.week_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.week_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.week_table.verticalHeader().setVisible(False)
        week_layout.addWidget(self.week_table)
        self.week_total_label = QLabel("Итого за неделю: 0 / 0")
        self.week_total_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        week_layout.addWidget(self.week_total_label)
        layout.addWidget(week_group)

        # Monthly progress bar
        month_group = QGroupBox("📈 Месячная динамика")
        month_layout = QVBoxLayout(month_group)
        self.month_bars = QVBoxLayout()
        month_layout.addLayout(self.month_bars)
        layout.addWidget(month_group)

        # Refresh button
        refresh_btn = QPushButton("🔄 Обновить статистику")
        refresh_btn.clicked.connect(self.refresh)
        layout.addWidget(refresh_btn)
        layout.addStretch()

    def refresh(self):
        from datetime import datetime, timedelta

        today = datetime.now().strftime("%Y-%m-%d")

        # Today stats
        items = database.get_all_items()
        today_completed = 0
        total_enabled = sum(1 for i in items if i["enabled"])
        for item in items:
            if item["enabled"] and database.is_completed_today(item["id"]):
                today_completed += 1

        self.today_done_label.setText(f"✅ Выполнено: {today_completed}")
        self.today_total_label.setText(f"📋 Всего: {total_enabled}")
        pct = (today_completed / total_enabled * 100) if total_enabled else 0
        self.today_pct_label.setText(f"{int(pct)}%")

        # Week stats
        week_data = database.get_week_stats()
        self.week_table.setRowCount(7)

        day_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        week_dates = {}
        for d in week_data.get("daily_data", []):
            week_dates[d["date"]] = d["done_count"]

        week_total = 0
        today_dt = datetime.now()
        start_of_week = today_dt - timedelta(days=today_dt.weekday())

        for i in range(7):
            date = (start_of_week + timedelta(days=i)).strftime("%Y-%m-%d")
            done = week_dates.get(date, 0)
            week_total += done
            self.week_table.setItem(i, 0, QTableWidgetItem(day_names[i]))
            done_item = QTableWidgetItem(str(done))
            if done > 0:
                done_item.setForeground(QColor("#51CF66"))
            self.week_table.setItem(i, 1, done_item)
            self.week_table.setItem(i, 2, QTableWidgetItem(str(total_enabled)))

        self.week_total_label.setText(f"Итого за неделю: {week_total} / {total_enabled * 7}")

        # Month bars (last 30 days)
        month_data = database.get_completion_stats(30)

        # Clear old bars
        while self.month_bars.count():
            item = self.month_bars.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if month_data:
            max_done = max(d["done_count"] for d in month_data) or 1
            for day_data in month_data[:14]:  # Last 14 days
                bar_layout = QHBoxLayout()
                date_label = QLabel(day_data["date"][5:])  # MM-DD
                date_label.setFixedWidth(50)
                bar = QProgressBar()
                bar.setRange(0, max(total_enabled, 1))
                bar.setValue(day_data["done_count"])
                bar.setTextVisible(True)
                bar.setFormat(f"{day_data['done_count']}/{total_enabled}")
                bar.setFixedHeight(20)
                pct = day_data["done_count"] / max(total_enabled, 1)
                if pct >= 0.8:
                    bar.setStyleSheet("QProgressBar::chunk { background-color: #51CF66; }")
                elif pct >= 0.5:
                    bar.setStyleSheet("QProgressBar::chunk { background-color: #FFA94D; }")
                else:
                    bar.setStyleSheet("QProgressBar::chunk { background-color: #FF6B6B; }")
                bar_layout.addWidget(date_label)
                bar_layout.addWidget(bar)
                self.month_bars.addLayout(bar_layout)


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
        total_label = QLabel("⚡ ПРОГРЕСС")
        total_label.setStyleSheet(f"color: {TEXT_NEON_CYAN}; font-size: 12px; font-weight: 600; letter-spacing: 2px;")
        progress_layout.addWidget(total_label)
        self.total_progress_bar = QProgressBar()
        self.total_progress_bar.setRange(0, 100)
        self.total_progress_bar.setTextVisible(True)
        self.total_progress_bar.setStyleSheet(f"""
            QProgressBar {{ border: 1px solid rgba(0, 245, 255, 0.15); border-radius: 6px;
            text-align: center; height: 28px; background-color: rgba(0, 245, 255, 0.03);
            color: {TEXT_NEON_WHITE}; font-size: 12px; font-weight: 600; font-family: {FONT_MONO}; }}
            QProgressBar::chunk {{ background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #5B3AFF, stop:0.5 #7B4CFF, stop:1 #00F5FF); border-radius: 5px; }}
        """)
        progress_layout.addWidget(self.total_progress_bar)
        self.refresh_btn = QPushButton("⟳")
        self.refresh_btn.setObjectName("success")
        self.refresh_btn.setToolTip("Обновить данные из Excel")
        self.refresh_btn.setFixedWidth(40)
        self.refresh_btn.setFixedHeight(28)
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
        self.goal_bars = []
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

        # Subtasks table
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
            self.today_text.setText(f"⚠️ Файл целей не найден на рабочем столе")
            logger.warning(f"Goals load failed: {e}")
            return

        # Total progress
        prog = data.get("total_progress", 0)
        self.total_progress_bar.setValue(int(prog))
        self.total_progress_bar.setFormat(f"{prog}%")

        # Colors for bars
        colors = ["#4A90D9", "#7B68EE", "#FF6B6B", "#51CF66", "#FFA94D", "#FF6B9D"]

        # Today schedule
        today_info = get_today_schedule()
        if today_info:
            d = today_info.get("date", "")
            date_str = d.strftime("%d.%m.%Y") if hasattr(d, "strftime") else ""
            text = f"📅 {date_str}  |  🔥 {today_info.get('priority', '')}"
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
                text += f"{emoji} {t['name']} — {t.get('deadline', '')}"
                if days < 0:
                    text += " (🔥 просрочено)"
                else:
                    text += f" (осталось {days} дн.)"
                text += "\n"
            self.urgent_text.setText(text)
        else:
            self.urgent_text.setText("✅ Срочных задач нет")
        # Goal progress bars
        color_map = {"1": "#4A90D9", "2": "#7B68EE", "3": "#FF6B6B",
                     "4": "#51CF66", "5": "#FFA94D", "6": "#FF6B9D"}
        for i, (label, bar) in enumerate(self.goal_bars):
            if i < len(data.get("goals", [])):
                goal = data["goals"][i]
                pct = goal.get("progress", 0)
                label.setText(str(goal["name"]))
                label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px; font-weight: 500;")
                bar.setValue(int(pct))
                bar.setFormat(f"{int(pct)}%")
                color = color_map.get(str(i+1), "#7170FF")
                bar.setStyleSheet(f"""
                    QProgressBar {{ border: 1px solid rgba(255,255,255,0.05); border-radius: 4px;
                    text-align: center; height: 24px; background-color: rgba(255,255,255,0.03);
                    color: {TEXT_SECONDARY}; font-size: 12px; font-weight: 500; }}
                    QProgressBar::chunk {{ background-color: {color}; border-radius: 3px; }}
                """)

        # Subtasks
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
            self.subtask_table.setItem(row, 3, QTableWidgetItem(f"{int(prog)}%"))
            status = task.get("status", "")
            status_item = QTableWidgetItem(status)
            if status.lower() in ("горит", "просрочено", "срочно"):
                status_item.setForeground(QColor("#FF4444"))
            elif status.lower() == "выполнено":
                status_item.setForeground(QColor("#44CC44"))
            self.subtask_table.setItem(row, 4, status_item)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Assistent denisa")
        self.setMinimumSize(850, 650)

        # Init DB
        database.init_db()

        # Auto-sync from goals if first run
        auto_sync()

        # Setup UI
        self.setup_ui()

        # Setup system tray
        self.setup_tray()

        # Start reminder engine (after tray is ready)
        self.engine = ReminderEngine()
        self.engine.notification_signal.connect(self.show_notification)
        self.engine.start()

        # Load data
        self.refresh_table()

        # Auto-refresh goals every 5 minutes
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.auto_refresh)
        self.refresh_timer.start(300000)

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # === LEFT PANEL: Avatar + voice control ===
        left_panel = QWidget()
        left_panel.setFixedWidth(220)
        left_panel.setStyleSheet(f"""
            QWidget {{
                background-color: {BG_SURFACE};
                border-right: 1px solid {BORDER_STANDARD};
            }}
        """)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        left_layout.setContentsMargins(12, 16, 12, 16)
        left_layout.setSpacing(12)

        # Avatar
        self.avatar_widget = AnimatedAvatarWidget()
        left_layout.addWidget(self.avatar_widget, alignment=Qt.AlignmentFlag.AlignCenter)

        # Status
        self.avatar_status = QLabel("● В сети")
        self.avatar_status.setStyleSheet(f"color: {BRAND_GREEN}; font-size: 11px;")
        left_layout.addWidget(self.avatar_status, alignment=Qt.AlignmentFlag.AlignCenter)

        # Mic button
        self.mic_btn = QPushButton("🎤 Говорить")
        self.mic_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mic_btn.setMinimumHeight(44)
        self.mic_btn.setObjectName("primary")
        self.mic_btn.clicked.connect(self.on_mic_click)
        left_layout.addWidget(self.mic_btn)

        # Voice status
        self.voice_status = QLabel("")
        self.voice_status.setStyleSheet(f"color: {TEXT_TERTIARY}; font-size: 11px;")
        self.voice_status.setWordWrap(True)
        self.voice_status.setMaximumWidth(190)
        left_layout.addWidget(self.voice_status, alignment=Qt.AlignmentFlag.AlignCenter)

        # Voice transcription display
        self.transcript_label = QLabel("")
        self.transcript_label.setStyleSheet(f"""
            color: {TEXT_NEON_CYAN}; font-size: 13px; font-weight: 600;
            background: rgba(100, 200, 255, 0.06);
            border-radius: 8px;
            padding: 8px;
        """)
        self.transcript_label.setWordWrap(True)
        self.transcript_label.setMaximumWidth(190)
        self.transcript_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.transcript_label.hide()
        left_layout.addWidget(self.transcript_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # STT status
        stt_status = []
        if WHISPER_AVAILABLE:
            stt_status.append("Whisper")
        if SR_AVAILABLE:
            stt_status.append("Google")
        if stt_status:
            stt_info = QLabel(f"🎤 {' + '.join(stt_status)}")
            stt_info.setStyleSheet(f"color: {TEXT_QUATERNARY}; font-size: 9px;")
            stt_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
            left_layout.addWidget(stt_info)

        left_layout.addStretch()
        main_layout.addWidget(left_panel)

        # === RIGHT: Tabs ===
        right_widget = QWidget()
        right_widget.setStyleSheet(f"background: {BG_PRIMARY};")
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()
        self.tabs.setFont(QFont("Segoe UI", 10))
        self.tabs.currentChanged.connect(self.on_tab_changed)

        # Tab 1: Schedule
        schedule_tab = QWidget()
        schedule_layout = QVBoxLayout(schedule_tab)
        self.setup_schedule_tab(schedule_layout)
        self.tabs.addTab(schedule_tab, "⏰ Расписание")

        # Tab 2: Goals
        self.goals_widget = GoalsWidget()
        self.tabs.addTab(self.goals_widget, "🎯 Цели 2026")

        # Tab 3: Stats
        self.stats_widget = StatsWidget()
        self.tabs.addTab(self.stats_widget, "📊 Статистика")

        # Tab 4: Focus
        self.focus_widget = FocusWidget()
        self.tabs.addTab(self.focus_widget, "🎯 Фокус")

        right_layout.addWidget(self.tabs)
        main_layout.addWidget(right_widget, stretch=1)

    def setup_schedule_tab(self, layout):
        # Top bar
        top_layout = QHBoxLayout()
        
        sync_btn = QPushButton("⟳ Синхр. с целями")
        sync_btn.setObjectName("success")
        sync_btn.setToolTip("Обновить расписание из файла целей")
        sync_btn.clicked.connect(self.resync_goals)
        top_layout.addWidget(sync_btn)

        settings_btn = QPushButton("⚡ Telegram")
        settings_btn.setObjectName("primary")
        settings_btn.clicked.connect(self.open_settings)
        top_layout.addWidget(settings_btn)
        top_layout.addStretch()
        layout.addLayout(top_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["✓", "⏰", "💬 Задача", "📅 Дни", "⚡"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        # Bottom buttons
        btn_layout = QHBoxLayout()
        
        add_btn = QPushButton("✦ Добавить")
        add_btn.setObjectName("primary")
        add_btn.clicked.connect(self.add_item)
        btn_layout.addWidget(add_btn)
        
        edit_btn = QPushButton("✎ Правка")
        edit_btn.clicked.connect(self.edit_item)
        btn_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("✕ Удалить")
        delete_btn.setObjectName("danger")
        delete_btn.clicked.connect(self.delete_item)
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

        stats_action = QAction("📊 Статистика", self)
        stats_action.triggered.connect(lambda: self.show_and_tab(2))
        tray_menu.addAction(stats_action)

        focus_action = QAction("🎯 Фокус", self)
        focus_action.triggered.connect(lambda: self.show_and_tab(3))
        tray_menu.addAction(focus_action)

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

    def on_tab_changed(self, index):
        if index == 1:  # Goals
            self.goals_widget.load_data()
        elif index == 2:  # Stats
            self.stats_widget.refresh()

    def auto_refresh(self):
        self.goals_widget.load_data()

    def resync_goals(self):
        """Re-sync schedule from goals file."""
        reply = QMessageBox.question(
            self, "Синхронизация",
            "Обновить расписание из файла целей? Текущие напоминания из целей будут заменены.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            database.delete_goal_items()
            database.set_setting("auto_schedule_synced", "0")
            auto_sync()
            self.refresh_table()

    def refresh_table(self):
        items = database.get_all_items()
        self.table.setRowCount(len(items))

        for row, item in enumerate(items):
            # Completion checkbox
            completed = database.is_completed_today(item["id"])
            check_item = QTableWidgetItem()
            check_item.setFlags(check_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            check_item.setCheckState(
                Qt.CheckState.Checked if completed else Qt.CheckState.Unchecked
            )
            check_item.setData(Qt.ItemDataRole.UserRole, item["id"])
            if completed:
                check_item.setBackground(QColor("#1a3a1a"))
            self.table.setItem(row, 0, check_item)

            # Time
            self.table.setItem(row, 1, QTableWidgetItem(item["time"]))

            # Text
            text_item = QTableWidgetItem(item["text"])
            if item.get("is_from_goals"):
                text_item.setForeground(QColor("#8888FF"))
            if completed:
                text_item.setForeground(QColor("#666666"))
                font = text_item.font()
                font.setStrikeOut(True)
                text_item.setFont(font)
            self.table.setItem(row, 2, text_item)

            # Days
            mask = item["days_mask"]
            days_str = ", ".join(
                DAY_NAMES[i] for i in range(7) if mask & (1 << i)
            )
            self.table.setItem(row, 3, QTableWidgetItem(days_str))

            # Enabled
            enabled_item = QTableWidgetItem()
            enabled_item.setFlags(enabled_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            enabled_item.setCheckState(
                Qt.CheckState.Checked if item["enabled"] else Qt.CheckState.Unchecked
            )
            enabled_item.setData(Qt.ItemDataRole.UserRole, item["id"])
            self.table.setItem(row, 4, enabled_item)

        # Disconnect previous handler to avoid duplicate signals
        try:
            self.table.itemChanged.disconnect()
        except TypeError:
            pass  # Not connected yet
        
        self.table.itemChanged.connect(self.on_item_changed)

    def on_item_changed(self, item):
        col = item.column()
        item_id = item.data(Qt.ItemDataRole.UserRole)
        if item_id is None:
            return

        if col == 0:  # Completion checkbox
            if item.checkState() == Qt.CheckState.Checked:
                database.mark_completed(item_id)
            else:
                database.unmark_completed(item_id)
            self.refresh_table()

        elif col == 4:  # Enabled checkbox
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


class FocusWidget(QWidget):
    """Pomodoro focus timer + motivation tab."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.focus_timer = FocusTimer()
        self.focus_timer.tick_signal.connect(self.on_tick)
        self.focus_timer.complete_signal.connect(self.on_session_complete)
        self.focus_timer.state_signal.connect(self.on_state_change)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)
        
        # Timer display
        timer_group = QGroupBox("⏱️ Таймер фокуса")
        timer_group.setStyleSheet(f"""
            QGroupBox {{ color: {TEXT_SECONDARY}; font-size: 14px; font-weight: 500;
            border: 1px solid {BORDER_STANDARD}; border-radius: 12px; margin-top: 8px; padding: 20px; }}
        """)
        timer_layout = QVBoxLayout(timer_group)
        timer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        timer_layout.setSpacing(15)
        
        self.timer_label = QLabel("25:00")
        self.timer_label.setStyleSheet(f"""
            font-size: 72px; font-weight: 200; color: {TEXT_PRIMARY};
            letter-spacing: 2px; font-family: 'Consolas', 'Courier New', monospace;
        """)
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        timer_layout.addWidget(self.timer_label)
        
        self.state_label = QLabel("Готов к работе 🚀")
        self.state_label.setStyleSheet(f"font-size: 16px; color: {TEXT_TERTIARY};")
        self.state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        timer_layout.addWidget(self.state_label)
        
        # Session info
        self.session_label = QLabel("Сегодня: 0 сессий • 0 минут фокуса")
        self.session_label.setStyleSheet(f"font-size: 13px; color: {TEXT_QUATERNARY};")
        self.session_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        timer_layout.addWidget(self.session_label)
        
        layout.addWidget(timer_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_layout.setSpacing(15)
        
        self.start_btn = QPushButton("▶️ Старт")
        self.start_btn.setObjectName("primary")
        self.start_btn.clicked.connect(self.toggle_focus)
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_layout.addWidget(self.start_btn)
        
        self.pause_btn = QPushButton("⏸️ Пауза")
        self.pause_btn.setStyleSheet("""
            QPushButton { background-color: rgba(255,255,255,0.05); color: #D0D6E0;
            border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 14px 30px; font-size: 14px; }
            QPushButton:hover { background-color: rgba(255,255,255,0.1); }
        """)
        self.pause_btn.clicked.connect(self.toggle_pause)
        self.pause_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.pause_btn.setEnabled(False)
        btn_layout.addWidget(self.pause_btn)
        
        layout.addLayout(btn_layout)
        
        # Motivation
        mot_group = QGroupBox("💪 Мотивация")
        mot_group.setStyleSheet(f"""
            QGroupBox {{ color: {TEXT_SECONDARY}; font-size: 14px; font-weight: 500;
            border: 1px solid {BORDER_STANDARD}; border-radius: 12px; margin-top: 8px; padding: 16px; }}
        """)
        mot_layout = QVBoxLayout(mot_group)
        self.motivation_text = QLabel("Выполни первую задачу, чтобы получить мотивацию! 🔥")
        self.motivation_text.setStyleSheet(f"font-size: 15px; color: {TEXT_TERTIARY}; line-height: 1.5;")
        self.motivation_text.setWordWrap(True)
        self.motivation_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mot_layout.addWidget(self.motivation_text)
        
        self.streak_label = QLabel("")
        self.streak_label.setStyleSheet(f"font-size: 13px; color: {TEXT_QUATERNARY};")
        self.streak_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mot_layout.addWidget(self.streak_label)
        layout.addWidget(mot_group)
        
        # Recommendation
        rec_group = QGroupBox("🤖 AI-рекомендация")
        rec_group.setStyleSheet(f"""
            QGroupBox {{ color: {TEXT_SECONDARY}; font-size: 14px; font-weight: 500;
            border: 1px solid {BORDER_STANDARD}; border-radius: 12px; margin-top: 8px; padding: 16px; }}
        """)
        rec_layout = QVBoxLayout(rec_group)
        self.rec_text = QLabel("Анализирую твою продуктивность...")
        self.rec_text.setStyleSheet(f"font-size: 14px; color: {TEXT_TERTIARY}; line-height: 1.6;")
        self.rec_text.setWordWrap(True)
        rec_layout.addWidget(self.rec_text)
        layout.addWidget(rec_group)
        
        layout.addStretch()
        
        # Initial load
        self.refresh_motivation()
    
    def toggle_focus(self):
        if self.focus_timer.current_mode == FocusMode.FOCUS and self.focus_timer.seconds_left > 0:
            self.focus_timer.stop()
            self.start_btn.setText("▶️ Старт")
            self.state_label.setText("Готов к работе 🚀")
            self.pause_btn.setEnabled(False)
            self.timer_label.setText("25:00")
        else:
            self.focus_timer.start_focus()
            self.start_btn.setText("⏹️ Стоп")
            self.pause_btn.setEnabled(True)
            self.state_label.setText("🧘 Фокусируемся...")
    
    def toggle_pause(self):
        if self.focus_timer._paused:
            self.focus_timer.resume()
            self.pause_btn.setText("⏸️ Пауза")
            self.state_label.setText("🧘 Фокусируемся...")
        else:
            self.focus_timer.pause()
            self.pause_btn.setText("▶️ Продолжить")
            self.state_label.setText("⏸️ На паузе")
    
    def on_tick(self, seconds: int, state: str):
        mins = seconds // 60
        secs = seconds % 60
        self.timer_label.setText(f"{mins:02d}:{secs:02d}")
    
    def on_state_change(self, state: str):
        if state == FocusMode.FOCUS:
            self.state_label.setText("🧘 Фокус! Не отвлекайся!")
        elif state == FocusMode.SHORT_BREAK:
            self.state_label.setText("☕ Короткий перерыв 5 мин")
        elif state == FocusMode.LONG_BREAK:
            self.state_label.setText("🌴 Длинный перерыв 15 мин")
    
    def on_session_complete(self, state: str):
        stats = self.focus_timer.get_stats()
        self.session_label.setText(f"Сегодня: {stats['today_sessions']} сессий • {stats['total_minutes']} минут фокуса")
        
        if state == FocusMode.FOCUS:
            # Try voice
            try:
                from voice_assistant import speak
                import threading
                threading.Thread(target=lambda: speak(
                    "Молодец, Денис! Фокус-сессия завершена. Отдохни немного."
                ), daemon=True).start()
            except:
                pass
            self.state_label.setText("✅ Фокус завершён! Молодец!")
            self.refresh_motivation()
        else:
            self.state_label.setText("▶️ Перерыв закончен! Снова в бой!")
    
    def refresh_motivation(self):
        try:
            from productivity_analytics import get_motivation, get_ai_recommendation, analyze_performance, get_day_status
            
            # Day status
            day_status = get_day_status()
            mot = get_motivation(day_status["done"], day_status["streak"])
            if mot:
                self.motivation_text.setText(f"{day_status['emoji']} {mot}")
                self.streak_label.setText(f"Серия: {day_status['streak']} дней • {day_status['done']}/{day_status['total']} задач ({day_status['percent']}%)")
            
            # AI recommendation
            rec = get_ai_recommendation()
            self.rec_text.setText(f"💡 {rec}")
            
            # Focus stats
            stats = self.focus_timer.get_stats()
            self.session_label.setText(f"Сегодня: {stats['today_sessions']} сессий • {stats['total_minutes']} минут фокуса")
            
        except Exception as e:
            logger.warning(f"Motivation refresh failed: {e}")

    # ============================================================
    # ГОЛОСОВОЙ АССИСТЕНТ — запись → STT → NLU → действие → TTS
    # ============================================================
    
    def on_mic_click(self):
        """Обработчик кнопки микрофона — запуск голосового ввода."""
        if hasattr(self, '_voice_active') and self._voice_active:
            self.voice_status.setText("Уже слушаю... Подожди")
            return
        
        self._voice_active = True
        self.mic_btn.setEnabled(False)
        self.mic_btn.setText("🎤 Слушаю...")
        self.voice_status.setText("🎙️ Говори команду...")
        self.transcript_label.hide()
        
        self.avatar_widget.set_mood("thinking")
        
        import threading
        thread = threading.Thread(target=self._voice_loop, daemon=True)
        thread.start()
    
    def _voice_loop(self):
        """Полный пайплайн: запись → распознавание → понимание → действие → ответ."""
        import time
        
        try:
            # === ШАГ 1: Запись с микрофона ===
            self._safe_status("🎙️ Слушаю...")
            audio_path = record_from_mic(duration=5)
            
            if not audio_path:
                self._safe_status("❌ Микрофон не работает. Проверь подключение.")
                self._safe_avatar_stop()
                return
            
            # === ШАГ 2: Распознавание речи ===
            self._safe_status("🧠 Распознаю речь...")
            text = None
            
            if WHISPER_AVAILABLE:
                text = transcribe_with_whisper(audio_path)
            
            if text is None and SR_AVAILABLE:
                text = transcribe_with_google(audio_path)
            
            # Cleanup temp file
            try:
                import os
                os.remove(audio_path)
            except:
                pass
            
            if not text:
                self._safe_status("🤷 Не расслышал. Попробуй ещё раз.")
                self._safe_avatar_stop()
                return
            
            text = text.strip().lower()
            logger.info(f"STT result: '{text}'")
            
            # Показываем распознанный текст
            self._safe_transcript(text)
            
            # === ШАГ 3: NLU — понимание команды ===
            self._safe_status("🤔 Анализирую команду...")
            command = parse_command(text)
            
            action = command.get("action", "unknown")
            confidence = command.get("confidence", 0)
            logger.info(f"NLU: action={action}, confidence={confidence}")
            
            if confidence < 0.2:
                self._safe_status(f"❓ Не понял команду: \"{text[:50]}\"")
                self._safe_speak("Извини, я не понял команду. Попробуй сказать по-другому.")
                self._safe_avatar_stop()
                return
            
            # === ШАГ 4: Выполнение действия ===
            self._safe_status(f"⚡ Выполняю: {action}")
            response = process_command(command)
            
            result_text = response.get("text", "Готово!")
            success = response.get("success", True)
            
            # === ШАГ 5: TTS ответ ===
            if success:
                self._safe_speak(result_text)
                self._safe_status(f"✅ {result_text[:60]}")
                
                # Аватар улыбается
                self._safe_avatar_mood("happy")
            else:
                self._safe_speak(f"Не получилось: {result_text[:80]}")
                self._safe_status(f"❌ {result_text[:60]}")
            
            # === ШАГ 6: Обновление GUI ===
            self._safe_refresh()
            
            # Отключаем анимацию рта через 2 секунды
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"Voice loop error: {e}")
            self._safe_status(f"⚠️ Ошибка: {str(e)[:50]}")
        finally:
            self._voice_active = False
            self._safe_mic_reset()
            self._safe_avatar_stop()
    
    # ---- Thread-safe helpers ----
    
    def _safe_status(self, text: str):
        """Thread-safe обновление статуса голоса."""
        from PyQt6.QtCore import QMetaObject, Qt, Q_ARG
        try:
            QMetaObject.invokeMethod(
                self.voice_status, "setText",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, text)
            )
        except RuntimeError:
            pass  # C++ object deleted
    
    def _safe_transcript(self, text: str):
        """Thread-safe показ распознанного текста."""
        from PyQt6.QtCore import QMetaObject, Qt, Q_ARG
        try:
            QMetaObject.invokeMethod(
                self.transcript_label, "setText",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, f'"{text}"')
            )
            QMetaObject.invokeMethod(
                self.transcript_label, "show",
                Qt.ConnectionType.QueuedConnection
            )
        except RuntimeError:
            pass
    
    def _safe_speak(self, text: str):
        """Thread-safe TTS в фоновом потоке."""
        try:
            # Включаем анимацию рта перед речью
            self.avatar_widget.set_speaking.emit(True)
            speak(text)
        except Exception as e:
            logger.warning(f"TTS failed: {e}")
        finally:
            self.avatar_widget.set_speaking.emit(False)
    
    def _safe_avatar_stop(self):
        """Thread-safe остановка анимации рта аватара."""
        try:
            self.avatar_widget.set_speaking.emit(False)
            self.avatar_widget.set_mood("neutral")
        except RuntimeError:
            pass
    
    def _safe_avatar_mood(self, mood: str):
        """Thread-safe смена настроения аватара."""
        try:
            self.avatar_widget.set_mood(mood)
        except RuntimeError:
            pass
    
    def _safe_mic_reset(self):
        """Thread-safe сброс кнопки микрофона."""
        from PyQt6.QtCore import QMetaObject, Qt, Q_ARG
        try:
            QMetaObject.invokeMethod(
                self.mic_btn, "setEnabled",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(bool, True)
            )
            QMetaObject.invokeMethod(
                self.mic_btn, "setText",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, "🎤 Говорить")
            )
        except RuntimeError:
            pass
    
    def _safe_refresh(self):
        """Thread-safe обновление таблицы."""
        from PyQt6.QtCore import QMetaObject, Qt
        try:
            QMetaObject.invokeMethod(
                self, "refresh_table",
                Qt.ConnectionType.QueuedConnection
            )
        except RuntimeError:
            pass


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Assistent denisa")
    
    # Apply NEON FUTURE theme
    from neon_theme import apply_neon_theme
    apply_neon_theme(app)
    
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
