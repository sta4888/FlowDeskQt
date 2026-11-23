"""Сборка Windows exe через PyInstaller.

    python scripts/build_exe.py              # один файл dist/ActivityTracker.exe
    python scripts/build_exe.py --onedir     # папка dist/ActivityTracker/ (быстрее стартует)
    python scripts/build_exe.py --dry-run    # только показать аргументы PyInstaller
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PKG = ROOT / "src" / "activity_tracker"
SEP = os.pathsep  # «;» на Windows, «:» на Linux/macOS


# бэкенды перехвата ввода и трея выбираются во время работы
WINDOWS_HIDDEN_IMPORTS = (
    [
        "--hidden-import", "pynput.keyboard._win32",
        "--hidden-import", "pynput.mouse._win32",
        "--hidden-import", "pystray._win32",
    ]
    if sys.platform == "win32"
    else []
)


def pyinstaller_args(onefile: bool) -> list[str]:
    return [
        str(PKG / "__main__.py"),
        "--name", "ActivityTracker",
        "--windowed",  # без консольного окна
        "--onefile" if onefile else "--onedir",
        "--noconfirm", "--clean",
        "--icon", str(PKG / "assets" / "app.ico"),
        "--paths", str(ROOT / "src"),
        # данные, которые читаются с диска во время работы
        "--add-data", f"{PKG / 'assets'}{SEP}activity_tracker/assets",
        "--add-data", f"{PKG / 'infrastructure' / 'db' / 'migrations'}{SEP}activity_tracker/infrastructure/db/migrations",
        # Модули, которые PyInstaller сам не увидит: env.py и миграции лежат как файлы данных
        # (их код не анализируется), а драйверы/бэкенды подгружаются динамически.
        "--hidden-import", "logging.config",  # нужен migrations/env.py
        "--hidden-import", "sqlalchemy.dialects.sqlite",
        "--collect-submodules", "alembic.ddl",
        *WINDOWS_HIDDEN_IMPORTS,
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--onedir", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    options = parser.parse_args()

    args = pyinstaller_args(onefile=not options.onedir)
    if options.dry_run:
        print("\n".join(args))
        return 0

    import PyInstaller.__main__ as pyinstaller

    pyinstaller.run(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
