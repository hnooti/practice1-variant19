"""Build ZIP fixtures from base64 manifests without external dependencies."""
import base64
import json
from pathlib import Path
import zipfile


def main():
    """Generate reproducible archives in the ignored vfs directory."""
    root = Path(__file__).resolve().parent.parent / "vfs"
    for source in root.glob("*.json"):
        target = source.with_suffix(".zip")
        with zipfile.ZipFile(target, "w") as archive:
            for name, data in json.loads(source.read_text()).items():
                info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
                archive.writestr(info, base64.b64decode(data, validate=True))


if __name__ == "__main__":
    main()
