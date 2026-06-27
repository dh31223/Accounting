"""交易模板管理面板。

- 模板列表（名称/类型/金额/分类/属性/账户/备注）
- 添加/编辑/删除模板
- 一键录入：从模板生成交易记录
"""

from datetime import date

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTreeWidget, QTreeWidgetItem, QPushButton, QLabel,
    QDialog, QFormLayout, QLineEdit, QDoubleSpinBox,
    QDateEdit, QComboBox, QMessageBox, QHeaderView,
    QAbstractItemView, QMenu, QButtonGroup, QRadioButton,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QCursor

from core.models import Template
from core.template import TemplateService
from db.schema import get_all_categories, get_all_accounts

ATTRIBUTE_LABELS = {
    "worthy": "💚 值得",
    "joy": "💛 悦己",
    "necessity": "📋 刚需",
    "waste": "🚫 浪费",
}


class TemplatePanel(QWidget):
    """交易模板管理面板。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(12)

        # 标题行
        header = QHBoxLayout()
        title = QLabel("📋 交易模板")
        title.setObjectName("pageTitle")
        header.addWidget(title)
        header.addStretch()

        add_btn = QPushButton("＋ 添加模板")
        add_btn.clicked.connect(lambda: self._open_dialog())
        header.addWidget(add_btn)

        layout.addLayout(header)

        # 模板列表
        self._tree = QTreeWidget()
        self._tree.setColumnCount(7)
        self._tree.setHeaderLabels(["名称", "类型", "金额", "分类", "属性", "账户", "备注"])
        self._tree.setRootIsDecorated(False)
        self._tree.setAlternatingRowColors(True)
        self._tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._on_context_menu)

        h = self._tree.header()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        h.setStretchLastSection(True)

        layout.addWidget(self._tree, stretch=1)

        # 底部操作栏
        footer = QHBoxLayout()
        footer.addStretch()

        self._apply_btn = QPushButton("⚡ 一键录入")
        self._apply_btn.setObjectName("btnSuccess")
        self._apply_btn.setToolTip("用选中的模板快速创建一笔交易")
        self._apply_btn.clicked.connect(self._on_apply)
        footer.addWidget(self._apply_btn)

        layout.addLayout(footer)

    def refresh(self):
        self._tree.clear()
        templates = TemplateService.get_all()
        for t in templates:
            item = QTreeWidgetItem(self._tree)
            item.setText(0, t.name)
            item.setText(1, "💰 收入" if t.type == "income" else "💸 支出")
            item.setText(2, f"¥{t.amount:,.2f}")
            item.setText(3, t.category)
            item.setText(4, ATTRIBUTE_LABELS.get(t.attribute, t.attribute))
            item.setText(5, t.account)
            item.setText(6, t.note or "")
            item.setData(0, Qt.ItemDataRole.UserRole, t.id)

    def _open_dialog(self, template: Template = None):
        dlg = TemplateDialog(self, template)
        dlg.adjustSize()
        if self.window():
            geo = self.window().frameGeometry()
            dlg_geo = dlg.frameGeometry()
            dlg_geo.moveCenter(geo.center())
            dlg.move(dlg_geo.topLeft())
        if dlg.exec() == TemplateDialog.DialogCode.Accepted:
            self.refresh()

    def _on_context_menu(self, pos):
        item = self._tree.itemAt(pos)
        if not item:
            return
        tid = item.data(0, Qt.ItemDataRole.UserRole)
        if tid is None:
            return

        menu = QMenu(self)
        menu.addAction("✏️ 编辑").triggered.connect(lambda: self._edit(tid))
        menu.addAction("⚡ 一键录入").triggered.connect(lambda: self._apply(tid))
        menu.addSeparator()
        menu.addAction("🗑 删除").triggered.connect(lambda: self._delete(tid))
        menu.exec(QCursor.pos())

    def _edit(self, tid: int):
        templates = TemplateService.get_all()
        target = next((t for t in templates if t.id == tid), None)
        if target:
            self._open_dialog(target)

    def _delete(self, tid: int):
        templates = TemplateService.get_all()
        target = next((t for t in templates if t.id == tid), None)
        if not target:
            return
        reply = QMessageBox.question(
            self, "确认删除", f"确定要删除模板「{target.name}」吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            TemplateService.delete(tid)
            self.refresh()

    def _on_apply(self):
        """一键录入选中模板。"""
        items = self._tree.selectedItems()
        if not items:
            QMessageBox.information(self, "提示", "请先选择一个模板")
            return
        tid = items[0].data(0, Qt.ItemDataRole.UserRole)
        if tid:
            self._apply(tid)

    def _apply(self, tid: int):
        """用模板创建交易。"""
        templates = TemplateService.get_all()
        target = next((t for t in templates if t.id == tid), None)
        if not target:
            return

        today = date.today().isoformat()
        reply = QMessageBox.question(
            self, "一键录入",
            f"使用模板「{target.name}」创建交易？\n\n"
            f"日期: {today}\n类型: {target.type}\n金额: ¥{target.amount:,.2f}\n"
            f"分类: {target.category}\n账户: {target.account}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                txn = TemplateService.apply_template(tid, today)
                if txn:
                    QMessageBox.information(self, "成功", f"交易已创建\n¥{txn.amount:,.2f} {txn.category}")
                else:
                    QMessageBox.warning(self, "错误", "模板不存在")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"创建失败: {e}")


class TemplateDialog(QDialog):
    """添加/编辑模板对话框。"""

    def __init__(self, parent, template: Template = None):
        super().__init__(parent)
        self._tmpl = template
        self._setup_ui()
        self._load_data()
        if template:
            self._populate(template)

    def _setup_ui(self):
        title = "编辑模板" if self._tmpl else "添加模板"
        self.setWindowTitle(title)
        self.setMinimumWidth(420)
        self.setModal(True)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 20, 24, 24)

        layout.addWidget(QLabel(title))
        layout.itemAt(layout.count() - 1).widget().setStyleSheet(
            "font-size:16px; font-weight:bold; color:#e2e8f0;")

        form = QFormLayout()
        form.setSpacing(12)

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("如「午饭外卖」")
        form.addRow("名称:", self._name_edit)

        self._type_income = QRadioButton("💰 收入")
        self._type_expense = QRadioButton("💸 支出")
        self._type_expense.setChecked(True)
        self._type_group = QButtonGroup(self)
        self._type_group.addButton(self._type_income, 0)
        self._type_group.addButton(self._type_expense, 1)
        self._type_group.buttonClicked.connect(self._on_type_changed)

        type_w = QWidget()
        type_l = QHBoxLayout(type_w)
        type_l.setContentsMargins(0, 0, 0, 0)
        type_l.addWidget(self._type_income)
        type_l.addWidget(self._type_expense)
        type_l.addStretch()
        form.addRow("类型:", type_w)

        self._amount_spin = QDoubleSpinBox()
        self._amount_spin.setRange(0.01, 99999999)
        self._amount_spin.setDecimals(2)
        self._amount_spin.setPrefix("¥ ")
        form.addRow("金额:", self._amount_spin)

        self._cat_combo = QComboBox()
        self._cat_combo.setEditable(True)
        self._cat_combo.setMaxVisibleItems(10)
        form.addRow("分类:", self._cat_combo)

        self._attr_combo = QComboBox()
        self._attr_combo.setMaxVisibleItems(6)
        for key, label in ATTRIBUTE_LABELS.items():
            self._attr_combo.addItem(label, key)
        self._attr_combo.setCurrentIndex(2)
        form.addRow("属性:", self._attr_combo)

        self._acct_combo = QComboBox()
        self._acct_combo.setEditable(True)
        self._acct_combo.setMaxVisibleItems(8)
        form.addRow("账户:", self._acct_combo)

        self._note_edit = QLineEdit()
        self._note_edit.setPlaceholderText("可选备注...")
        form.addRow("备注:", self._note_edit)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel = QPushButton("取消")
        cancel.setObjectName("btnSecondary")
        cancel.clicked.connect(self.reject)
        btn_layout.addWidget(cancel)
        save = QPushButton("保存")
        save.clicked.connect(self._on_save)
        btn_layout.addWidget(save)
        layout.addLayout(btn_layout)

    def _load_data(self):
        cats = get_all_categories()
        self._cat_combo.clear()
        for name in cats.get("expense", []):
            self._cat_combo.addItem(name)
        self._cat_combo.setCurrentIndex(0)

        for acc in get_all_accounts():
            self._acct_combo.addItem(acc)

    def _on_type_changed(self):
        self._cat_combo.clear()
        cats = get_all_categories()
        key = "income" if self._type_income.isChecked() else "expense"
        for name in cats.get(key, []):
            self._cat_combo.addItem(name)

    def _populate(self, t: Template):
        self._name_edit.setText(t.name)
        if t.type == "income":
            self._type_income.setChecked(True)
        self._on_type_changed()
        self._amount_spin.setValue(t.amount)
        idx = self._cat_combo.findText(t.category)
        if idx >= 0:
            self._cat_combo.setCurrentIndex(idx)
        idx = self._attr_combo.findData(t.attribute)
        if idx >= 0:
            self._attr_combo.setCurrentIndex(idx)
        idx = self._acct_combo.findText(t.account)
        if idx >= 0:
            self._acct_combo.setCurrentIndex(idx)
        self._note_edit.setText(t.note or "")

    def _on_save(self):
        name = self._name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "输入错误", "请输入模板名称")
            return
        if self._amount_spin.value() <= 0:
            QMessageBox.warning(self, "输入错误", "金额必须大于 0")
            return

        tmpl = Template(
            name=name,
            type="income" if self._type_income.isChecked() else "expense",
            amount=self._amount_spin.value(),
            category=self._cat_combo.currentText().strip(),
            attribute=self._attr_combo.currentData(),
            account=self._acct_combo.currentText().strip(),
            note=self._note_edit.text().strip(),
        )

        try:
            if self._tmpl and self._tmpl.id is not None:
                tmpl.id = self._tmpl.id
                TemplateService.update(tmpl)
            else:
                TemplateService.create(tmpl)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {e}")
