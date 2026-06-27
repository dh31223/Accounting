"""数据库备份与还原模块。

支持一键备份 SQLite 数据库文件和从备份文件还原。
"""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from db.connection import DB_PATH, db_exists, get_connection, close_connection


class BackupService:
    """备份与还原服务。"""

    @staticmethod
    def backup(backup_dir: Optional[str] = None) -> str:
        """备份数据库文件。

        Args:
            backup_dir: 备份目录，默认为项目根目录下的 backups/

        Returns:
            备份文件的路径
        """
        if not db_exists():
            raise FileNotFoundError(f"数据库文件不存在: {DB_PATH}")

        dest_dir = Path(backup_dir) if backup_dir else DB_PATH.parent / "backups"
        dest_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"accounting_backup_{timestamp}.db"
        backup_path = dest_dir / backup_name

        # 先执行 checkpoint 确保 WAL 数据写入主文件
        conn = get_connection()
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        close_connection(conn)

        shutil.copy2(str(DB_PATH), str(backup_path))
        return str(backup_path)

    @staticmethod
    def restore(backup_path: str) -> bool:
        """从备份文件还原数据库。

        当前数据库将被替换。还原前会自动备份当前数据库（以 .pre_restore 结尾）。

        Args:
            backup_path: 备份文件的路径

        Returns:
            True 如果还原成功
        """
        backup_file = Path(backup_path)
        if not backup_file.exists():
            raise FileNotFoundError(f"备份文件不存在: {backup_path}")

        # 1. 如果当前有数据库，先做个安全备份
        if db_exists():
            safety_backup = str(DB_PATH) + ".pre_restore"
            shutil.copy2(str(DB_PATH), safety_backup)

        # 2. 关闭所有连接后替换
        shutil.copy2(str(backup_file), str(DB_PATH))
        return True

    @staticmethod
    def list_backups(backup_dir: Optional[str] = None) -> list[dict]:
        """列出所有备份文件。

        Returns:
            [{'name': '...', 'path': '...', 'size': 12345, 'time': '...'}, ...]
        """
        dest_dir = Path(backup_dir) if backup_dir else DB_PATH.parent / "backups"
        if not dest_dir.exists():
            return []

        backups = []
        for f in sorted(dest_dir.glob("accounting_backup_*.db"), reverse=True):
            stat = f.stat()
            backups.append({
                "name": f.name,
                "path": str(f),
                "size": stat.st_size,
                "time": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            })
        return backups
