import shutil
import sqlite3
import zipfile
from pathlib import Path


def main():
    backups = sorted(Path("backups").glob("t2way_backup_*.zip"))

    if not backups:
        print("Бэкапов не найдено")
        return

    target = backups[-1]
    print(f"Проверяем последний бэкап: {target}")

    with zipfile.ZipFile(target) as archive:
        archive.extract("t2way.sqlite3", "backups/_check")

    con = sqlite3.connect("backups/_check/t2way.sqlite3")
    print("integrity_check:", con.execute("PRAGMA integrity_check").fetchone()[0])

    tables = [
        row[0]
        for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'")
    ]
    print("таблицы:", ", ".join(tables))

    users = con.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    trainings = con.execute("SELECT COUNT(*) FROM trainings").fetchone()[0]
    print(f"записей: users={users}, trainings={trainings}")

    con.close()

    shutil.rmtree("backups/_check", ignore_errors=True)
    print("Проверка завершена, временные файлы удалены")


if __name__ == "__main__":
    main()