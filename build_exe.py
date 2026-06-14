import importlib.util
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ENTRY_FILE = ROOT / "translator_v6.pyw"
ICON_FILE = ROOT / "assets" / "monstranslate_icon.ico"
ASSETS_DIR = ROOT / "assets"


def main():
    if not ENTRY_FILE.exists():
        print("translator_v6.pyw bulunamadı.")
        return 1

    if importlib.util.find_spec("PyInstaller") is None:
        print("PyInstaller kurulu değil.")
        print("Kurulum için: pip install -r requirements-build.txt")
        return 1

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--name",
        "MonsTranslate",
        "--icon",
        str(ICON_FILE),
        "--add-data",
        f"{ASSETS_DIR};assets",
        str(ENTRY_FILE),
    ]
    result = subprocess.run(command, cwd=ROOT)
    if result.returncode == 0:
        print("Exe hazır: dist/MonsTranslate.exe")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
