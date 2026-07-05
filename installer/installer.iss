; ============================================================
; Inno Setup 安装脚本 — Accounting 个人记账软件
; ============================================================
; 使用方法（在 Windows 上）:
;   1. 先运行 PyInstaller 打包: pyinstaller installer/Accounting.spec
;   2. 打开 Inno Setup Compiler，加载本文件，点击 Compile
;   3. 安装包生成在 installer\Output\ 目录
;
; 下载 Inno Setup: https://jrsoftware.org/isinfo.php
; ============================================================

#define MyAppName "Accounting - 个人记账"
#define MyAppNameEn "Accounting"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Personal"
#define MyAppURL "https://github.com/user/accounting"
#define MyAppExeName "Accounting.exe"

[Setup]
; 安装包基础信息
AppId={{B8F4A3D2-7E6C-4A1B-9D5F-2C8A7E3B1F0D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; 默认安装路径（用户可修改）
DefaultDirName={autopf}\{#MyAppNameEn}

; 开始菜单文件夹（设为 "Accounting"）
DefaultGroupName={#MyAppNameEn}

; 不允许用户选择 "为所有用户安装" vs "仅当前用户" — 简化为仅当前用户
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; 输出路径
OutputDir=Output
OutputBaseFilename=Accounting-Setup-{#MyAppVersion}

; 安装包外观
SetupIconFile=app.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}

; 压缩
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern

; 要求管理员权限时弹出 UAC 提示（仅当用户选择安装到 Program Files 时）
; PrivilegesRequired=lowest 表示默认不需要管理员

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
; 桌面快捷方式（默认勾选）
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加快捷方式:"; Flags: checkedonce

[Files]
; 主程序 — 从 PyInstaller 的 dist 目录复制
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; 可选：APIKey.txt 模板（如果存在）
Source: "..\APIKey.txt.example"; DestDir: "{app}"; Flags: ignoreversion; DestName: "APIKey.txt.example"

; 注意: 数据库文件 accounting.db 不打包 — 首次运行时自动创建

[Icons]
; 开始菜单快捷方式
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
; 桌面快捷方式（用户可选）
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
; 卸载快捷方式
Name: "{group}\卸载 Accounting"; Filename: "{uninstallexe}"

[Run]
; 安装完成后询问是否启动
Filename: "{app}\{#MyAppExeName}"; Description: "启动 Accounting 个人记账"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; 卸载时询问是否删除用户数据
Type: filesandordirs; Name: "{app}"

[Code]
// 卸载时询问是否保留数据
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usUninstall then
  begin
    if MsgBox('是否同时删除所有记账数据（数据库、API Key 等）？' + #13#10#13#10 +
              '选"是"将彻底清除一切数据。' + #13#10 +
              '选"否"将保留数据文件，方便以后重新安装时恢复。',
              mbConfirmation, MB_YESNO) = IDYES then
    begin
      // 删除数据目录中的文件
      DeleteFile(ExpandConstant('{app}\accounting.db'));
      DeleteFile(ExpandConstant('{app}\accounting.db-wal'));
      DeleteFile(ExpandConstant('{app}\accounting.db-shm'));
      DeleteFile(ExpandConstant('{app}\APIKey.txt'));
      DelTree(ExpandConstant('{app}\backups'), True, True, True);
    end;
  end;
end;
