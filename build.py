"""Copy package files into the release layout and create dist/katanazero.zip."""
from pathlib import Path
import shutil
import tempfile
import zipfile

root = Path(__file__).resolve().parent
package = root / "package"
destination = root / "dist/katanazero.zip"
destination.parent.mkdir(exist_ok=True)
executables = {"Katana ZERO.sh", "gmloadernext.aarch64", "splash", "patchscript", "android_compat.py"}

with tempfile.TemporaryDirectory(dir=destination.parent) as temporary:
    staging = Path(temporary)
    assert staging.resolve().is_relative_to(destination.parent.resolve())
    shutil.copytree(package / "katanazero", staging / "katanazero")
    shutil.copy2(package / "Katana ZERO.sh", staging / "Katana ZERO.sh")
    for name in ("README.md", "port.json", "gameinfo.xml", "cover.png", "screenshot.png"):
        shutil.copy2(package / name, staging / "katanazero" / name)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(staging.rglob("*")):
            if path.is_file():
                info = zipfile.ZipInfo.from_file(path, path.relative_to(staging).as_posix())
                info.create_system = 3
                info.external_attr = (0o100755 if path.name in executables else 0o100644) << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, path.read_bytes())

print(destination)
