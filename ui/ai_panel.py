"""AI 预算建议面板。

- DeepSeek API Key 设置
- 可自定义系统提示词
- 获取建议按钮 + 加载动画
- Markdown 结果展示
"""

import os
import threading

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QLineEdit,
    QMessageBox, QGroupBox, QProgressBar, QApplication,
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject

from core.ai_suggest import get_suggestions_sync, DEFAULT_SYSTEM_PROMPT


class AIWorker(QObject):
    """后台工作线程，避免阻塞 UI。"""
    finished = pyqtSignal(str)   # result text
    error = pyqtSignal(str)      # error message

    def __init__(self, api_key: str, system_prompt: str, months: int):
        super().__init__()
        self._api_key = api_key
        self._system_prompt = system_prompt
        self._months = months

    def run(self):
        try:
            result = get_suggestions_sync(
                self._api_key, self._system_prompt, self._months
            )
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class AIPanel(QWidget):
    """AI 预算建议面板。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = None
        self._worker_thread = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(16)

        title = QLabel("🤖 AI 预算建议")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        # ---- API Key ----
        key_group = QGroupBox("🔑 DeepSeek API Key")
        key_group.setStyleSheet(
            "QGroupBox { color: #e2e8f0; font-size:14px; font-weight:bold; "
            "border: 1px solid #2d3a5c; border-radius: 10px; margin-top: 14px; "
            "padding: 18px 14px 12px 14px; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 14px; padding: 0 8px; }"
        )
        key_layout = QHBoxLayout(key_group)
        key_layout.setSpacing(10)

        self._api_key_input = QLineEdit()
        self._api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._api_key_input.setPlaceholderText("sk-...")
        # 优先读环境变量
        env_key = os.environ.get("DEEPSEEK_API_KEY", "")
        if env_key:
            self._api_key_input.setText(env_key)
        key_layout.addWidget(self._api_key_input, stretch=1)

        save_key_btn = QPushButton("保存")
        save_key_btn.setObjectName("btnSmall")
        save_key_btn.clicked.connect(self._save_key)
        key_layout.addWidget(save_key_btn)

        layout.addWidget(key_group)

        # ---- 提示词 ----
        prompt_group = QGroupBox("📝 系统提示词（可自定义）")
        prompt_group.setStyleSheet(
            "QGroupBox { color: #e2e8f0; font-size:14px; font-weight:bold; "
            "border: 1px solid #2d3a5c; border-radius: 10px; margin-top: 14px; "
            "padding: 18px 14px 12px 14px; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 14px; padding: 0 8px; }"
        )
        prompt_layout = QVBoxLayout(prompt_group)
        prompt_layout.setSpacing(8)

        self._prompt_edit = QTextEdit()
        self._prompt_edit.setPlainText(DEFAULT_SYSTEM_PROMPT)
        self._prompt_edit.setMaximumHeight(200)
        self._prompt_edit.setPlaceholderText("自定义系统提示词...")
        prompt_layout.addWidget(self._prompt_edit)

        reset_btn = QPushButton("恢复默认")
        reset_btn.setObjectName("btnSmall")
        reset_btn.clicked.connect(lambda: self._prompt_edit.setPlainText(DEFAULT_SYSTEM_PROMPT))
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(reset_btn)
        prompt_layout.addLayout(btn_row)

        layout.addWidget(prompt_group)

        # ---- 执行按钮 + 进度条 ----
        action_row = QHBoxLayout()
        action_row.setSpacing(12)

        self._run_btn = QPushButton("🚀 获取 AI 建议")
        self._run_btn.clicked.connect(self._on_run)
        action_row.addWidget(self._run_btn)

        self._progress = QProgressBar()
        self._progress.setRange(0, 0)  # 不确定进度
        self._progress.setVisible(False)
        self._progress.setMaximumWidth(200)
        action_row.addWidget(self._progress)

        action_row.addStretch()
        layout.addLayout(action_row)

        # ---- 结果展示 ----
        result_label = QLabel("💡 AI 建议结果")
        result_label.setStyleSheet("font-size:14px; font-weight:bold; color:#e2e8f0;")
        layout.addWidget(result_label)

        self._result_view = QTextEdit()
        self._result_view.setReadOnly(True)
        self._result_view.setPlaceholderText("点击上方按钮获取 AI 预算建议...")
        self._result_view.setMarkdown("")
        layout.addWidget(self._result_view, stretch=1)

    def _save_key(self):
        """保存 API Key 到环境变量（会话级别）。"""
        key = self._api_key_input.text().strip()
        if key:
            os.environ["DEEPSEEK_API_KEY"] = key
            QMessageBox.information(self, "已保存", "API Key 已保存（本次会话有效）")
        else:
            QMessageBox.warning(self, "提示", "请输入有效的 API Key")

    def _on_run(self):
        """启动 AI 建议获取。"""
        api_key = self._api_key_input.text().strip()
        if not api_key:
            QMessageBox.warning(self, "提示", "请先设置 DeepSeek API Key")
            return

        # 把 key 存到环境变量以便后续使用
        os.environ["DEEPSEEK_API_KEY"] = api_key

        self._run_btn.setEnabled(False)
        self._progress.setVisible(True)
        self._result_view.setPlainText("正在调用 DeepSeek API，请稍候...")

        prompt = self._prompt_edit.toPlainText().strip()
        if not prompt:
            prompt = DEFAULT_SYSTEM_PROMPT

        # 后台线程执行
        self._worker = AIWorker(api_key, prompt, 3)
        self._worker_thread = threading.Thread(target=self._worker.run, daemon=True)
        self._worker.finished.connect(self._on_result)
        self._worker.error.connect(self._on_error)
        self._worker_thread.start()

    def _on_result(self, text: str):
        """接收 AI 结果。"""
        self._run_btn.setEnabled(True)
        self._progress.setVisible(False)
        self._result_view.setMarkdown(text)

    def _on_error(self, error_msg: str):
        """处理错误。"""
        self._run_btn.setEnabled(True)
        self._progress.setVisible(False)
        self._result_view.setPlainText(f"❌ 错误: {error_msg}")
