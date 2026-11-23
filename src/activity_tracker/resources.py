from pathlib import Path

ASSETS_DIR = Path(__file__).parent / "assets"


def asset_path(name: str) -> Path:
    """Путь к файлу в assets. Работает и из исходников, и из собранного PyInstaller exe."""
    return ASSETS_DIR / name
