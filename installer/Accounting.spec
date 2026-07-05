# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置 — Accounting 个人记账软件

使用方法（在 Windows 上执行）:
    pip install pyinstaller
    pyinstaller installer/Accounting.spec

产物在 dist/ 目录下。
"""

import sys
from pathlib import Path

# ---- 基础配置 ----
APP_NAME = "Accounting"
ENTRY_SCRIPT = str(Path(__file__).resolve().parent.parent / "main.py")
ICON_FILE = str(Path(__file__).resolve().parent / "app.ico")

# ---- 隐藏导入（PyInstaller 可能检测不到的模块） ----
hiddenimports = [
    # PyQt6 平台插件
    "PyQt6.QtCore",
    "PyQt6.QtGui",
    "PyQt6.QtWidgets",
    # matplotlib 后端
    "matplotlib.backends.backend_qtagg",
    "matplotlib.backends.backend_qt5agg",
    "matplotlib.figure",
    # openpyxl
    "openpyxl",
    "openpyxl.styles",
    "openpyxl.utils",
    # httpx
    "httpx",
    # 标准库中 PyInstaller 可能漏掉的
    "sqlite3",
    "asyncio",
    "json",
    "pathlib",
]

# ---- matplotlib 数据文件收集 ----
datas = [
    # matplotlib 自带数据（字体等）
    (str(Path(sys.prefix) / "Lib" / "site-packages" / "matplotlib" / "mpl-data"),
     "matplotlib/mpl-data"),
]

# ---- Qt 平台插件（关键！否则 PyQt6 无法启动） ----
# PyInstaller 6.x+ 通常自动处理，以下为保险项
binaries = []

# 可选图标（如果 app.ico 存在则使用）
icon_path = ICON_FILE if Path(ICON_FILE).exists() else None

# ============================================================
# Analysis
# ============================================================
a = Analysis(
    [ENTRY_SCRIPT],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

# ============================================================
# PYZ
# ============================================================
pyz = PYZ(a.pure)

# ============================================================
# EXE — 单文件，窗口模式（不弹控制台）
# ============================================================
exe_kwargs = dict(
    name=APP_NAME,
    console=False,          # 不显示命令行窗口
    strip=False,
    upx=True,               # UPX 压缩减小体积
    runtime_tmpdir=None,
)

if icon_path:
    exe_kwargs["icon"] = icon_path

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    **exe_kwargs,
)
