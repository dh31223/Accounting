"""设置页面。

包含：
- Excel 导出（日期范围 + 文件保存对话框）
- 数据库备份/还原
"""

import os
from datetime import date, timedelta

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QDateEdit, QComboBox, QPushButton, QLabel,
    QFileDialog, QMessageBox, QListWidget, QListWidgetItem,
    QGroupBox, QAbstractItemView,
)
from PyQt6.QtCore import Qt, QDate

from core.export import ExportService
from core.backup import BackupService


class SettingsPage(QWidget):
    """设置页面。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(16)

        title = QLabel("⚙️ 设置")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        # ---- Excel 导出 ----
        export_group = QGroupBox("📥 Excel 导出")
        export_group.setStyleSheet(
            "QGroupBox { color: #e2e8f0; font-size:15px; font-weight:bold; "
            "border: 1px solid #2d3a5c; border-radius: 10px; margin-top: 16px; padding: 20px 16px 16px 16px; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 16px; padding: 0 8px; }"
        )
        export_layout = QVBoxLayout(export_group)
        export_layout.setSpacing(10)

        date_row = QHBoxLayout()
        date_row.setSpacing(10)
        self._add_label(date_row, "从")
        self._export_from = QDateEdit()
        self._export_from.setCalendarPopup(True)
        self._export_from.setDisplayFormat("yyyy-MM-dd")
        self._export_from.setDate(QDate.currentDate().addMonths(-1))
        self._export_from.setMinimumWidth(130)
        date_row.addWidget(self._export_from)

        self._add_label(date_row, "至")
        self._export_to = QDateEdit()
        self._export_to.setCalendarPopup(True)
        self._export_to.setDisplayFormat("yyyy-MM-dd")
        self._export_to.setDate(QDate.currentDate())
        self._export_to.setMinimumWidth(130)
        date_row.addWidget(self._export_to)
        date_row.addStretch()

        self._export_btn = QPushButton("📥 导出 Excel")
        self._export_btn.clicked.connect(self._on_export)
        date_row.addWidget(self._export_btn)

        export_layout.addLayout(date_row)

        layout.addWidget(export_group)

        # ---- 备份/还原 ----
        backup_group = QGroupBox("💾 数据库备份与还原")
        backup_group.setStyleSheet(
            "QGroupBox { color: #e2e8f0; font-size:15px; font-weight:bold; "
            "border: 1px solid #2d3a5c; border-radius: 10px; margin-top: 16px; padding: 20px 16px 16px 16px; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 16px; padding: 0 8px; }"
        )
        backup_layout = QVBoxLayout(backup_group)
        backup_layout.setSpacing(10)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        backup_btn = QPushButton("💾 立即备份")
        backup_btn.clicked.connect(self._on_backup)
        btn_row.addWidget(backup_btn)

        restore_btn = QPushButton("📂 还原备份")
        restore_btn.clicked.connect(self._on_restore)
        btn_row.addWidget(restore_btn)

        btn_row.addStretch()
        backup_layout.addLayout(btn_row)

        # 备份列表
        backup_layout.addWidget(QLabel("历史备份:"))
        self._backup_list = QListWidget()
        self._backup_list.setMaximumHeight(200)
        self._backup_list.setAlternatingRowColors(True)
        self._refresh_backup_list()
        backup_layout.addWidget(self._backup_list)

        layout.addWidget(backup_group)

        layout.addStretch()

    def _add_label(self, layout, text: str):
        label = QLabel(f"{text}:")
        label.setStyleSheet("background:transparent; color:#94a3b8; font-size:13px; border:none;")
        layout.addWidget(label)

    # ---- 导出 ----

    def _on_export(self):
        start = self._export_from.date().toString("yyyy-MM-dd")
        end = self._export_to.date().toString("yyyy-MM-dd")

        path, _ = QFileDialog.getSaveFileName(
            self, "导出 Excel", f"记账导出_{start}_{end}.xlsx",
            "Excel 文件 (*.xlsx)"
        )
        if not path:
            return

        try:
            ExportService.export_transactions(path, start, end)
            QMessageBox.information(self, "导出成功", f"已导出到:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"错误: {e}")

    # ---- 备份/还原 ----

    def _on_backup(self):
        try:
            dest = BackupService.backup()
            self._refresh_backup_list()
            QMessageBox.information(self, "备份成功", f"备份已保存到:\n{dest}")
        except Exception as e:
            QMessageBox.critical(self, "备份失败", f"错误: {e}")

    def _on_restore(self):
        reply = QMessageBox.warning(
            self, "⚠ 还原备份",
            "还原备份将覆盖当前数据库！\n\n"
            "系统会先自动备份当前数据库再还原。\n"
            "确定要继续吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        # 让用户选择备份文件
        path, _ = QFileDialog.getOpenFileName(
            self, "选择备份文件", "backups",
            "SQLite 数据库 (*.db);;所有文件 (*)"
        )
        if not path:
            return

        try:
            BackupService.restore(path)
            self._refresh_backup_list()
            QMessageBox.information(
                self, "还原成功",
                "数据库已从备份还原。\n请重启应用以生效。"
            )
        except Exception as e:
            QMessageBox.critical(self, "还原失败", f"错误: {e}")

    def _refresh_backup_list(self):
        self._backup_list.clear()
        try:
            backups = BackupService.list_backups()
            for b in backups:
                size_kb = b.get("size", 0) / 1024
                time_str = b.get("time", "")
                item = QListWidgetItem(
                    f"{b.get('name', '')}  |  {size_kb:.1f} KB  |  {time_str}"
                )
                self._backup_list.addItem(item)
        except Exception:
            pass
