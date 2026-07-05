# Windows 打包指南

将 Accounting 个人记账软件打包为 `.exe` 安装包，发给别人双击即可安装。

---

## 方法一：GitHub Actions 云构建（推荐 ⭐）

**不需要 Windows 电脑**。把代码推到 GitHub，云端自动打包，下载安装包即可。

### 1. 推送代码到 GitHub

```bash
git remote add origin git@github.com:你的用户名/Accounting.git
git push -u origin master
```

### 2. 触发构建

- **自动触发**：推送代码后自动开始
- **手动触发**：GitHub 仓库页面 → Actions → Build Windows Installer → Run workflow

### 3. 下载安装包

构建完成后（约 5-8 分钟）：

1. 打开 GitHub 仓库页面 → **Actions** 标签
2. 点击最新的 **Build Windows Installer** 运行记录
3. 在页面底部的 **Artifacts** 区域，点击 **Accounting-Setup** 下载

下载得到一个 `.zip`，解压后就是 `Accounting-Setup-1.0.0.exe`。

> 发给别人这个 exe 文件，双击安装，不需要装任何东西。

---

## 方法二：本地 Windows 打包

如果你有 Windows 电脑，可以本地打包。

### 前置准备

```powershell
# 1. 安装 Python 3.12+ (python.org)，勾选 "Add Python to PATH"
python --version

# 2. 安装依赖
pip install -r requirements.txt
pip install pyinstaller Pillow

# 3. 安装 Inno Setup (https://jrsoftware.org/isinfo.php)
```

### 打包步骤

```powershell
# 1. 生成图标
python installer/generate_icon.py

# 2. PyInstaller 打包
pyinstaller installer/Accounting.spec
# → 产物: dist/Accounting.exe

# 3. Inno Setup 生成安装包
# 打开 Inno Setup Compiler → File → Open → installer/installer.iss → Build → Compile
# → 产物: installer/Output/Accounting-Setup-1.0.0.exe
```

---

## 安装包特性

用户安装 `Accounting-Setup-1.0.0.exe` 时：

| 特性 | 说明 |
|------|------|
| 安装路径选择 | 默认 `C:\Users\<用户>\AppData\Local\Programs\Accounting`，可自定义 |
| 开始菜单快捷方式 | 自动创建，含启动程序和卸载入口 |
| 桌面快捷方式 | 可选（默认勾选） |
| 卸载 | Windows 设置 → 应用 → 卸载（开始菜单也有卸载快捷方式） |
| 数据保留 | 卸载时询问是否删除记账数据，选"否"则数据保留 |

### 用户数据存储

```
C:\Users\<用户名>\AppData\Roaming\Accounting\
├── accounting.db          # 数据库
├── APIKey.txt             # API Key
└── backups\               # 备份文件
```

升级/重装软件不会丢失数据。

---

## 常见问题

### Q: 要发给别人，只发 exe 就行吗？

对，一个 `Accounting-Setup-1.0.0.exe` 就够了。对方不需要 Python 或任何依赖。

### Q: 安装包有多大？

约 40-60 MB（lzma2 压缩后），EXE 本体约 60-80 MB（含完整 Python 运行时）。

### Q: 杀毒软件报警？

PyInstaller 打包偶尔被误报。如需正式分发，可购买代码签名证书签名。
