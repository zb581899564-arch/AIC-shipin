"""Install only small source dependencies under a new pilot root, never the env."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
import traceback
import zipfile

from provenance import download_source, write_new

SOURCES = {
    "pytorchvideo": ("facebookresearch/pytorchvideo", "2ac6ed361309cb25144636ad82dd8bd6a4970e0c"),
    "UMT": ("TencentARC/UMT", "bde05e3de39049bf90d8807f6b2a4ed8b42acbb0"),
}
SMALL_DEPENDENCIES = [
    "nncore==0.3.7", "fvcore==0.1.5.post20221221", "iopath==0.1.10",
    "yacs==0.1.8", "termcolor==1.1.0", "portalocker==2.10.1", "terminaltables==3.1.10",
]


def unpack_code(archive, destination):
    destination.mkdir()
    base = destination.resolve()
    with zipfile.ZipFile(archive) as package:
        if package.testzip() is not None:
            raise ValueError("Corrupt source archive")
        for member in package.infolist():
            relative = Path(*Path(member.filename).parts[1:])
            target = (destination / relative).resolve()
            if not target.is_relative_to(base) or (member.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError("Unsafe source member")
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            elif relative.parts:
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open("xb") as stream:
                    stream.write(package.read(member))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    started = time.monotonic()
    root = args.root.resolve()
    write_new(root / "bootstrap_claim.json", dict(argv=sys.argv, scope="CODE_ONLY_NO_WEIGHTS"))
    sources = root / "sources"
    sources.mkdir()
    receipts = []
    for name, (repo, commit) in SOURCES.items():
        url = f"https://codeload.github.com/{repo}/zip/{commit}"
        archive = sources / f"{name}.zip"
        receipt = download_source(url, archive, 12_000_000)
        unpack_code(archive, sources / name)
        receipts.append(dict(name=name, commit=commit, **receipt))
        write_new(sources / f"{name}_receipt.json", receipts[-1])
    target = root / "dependencies"
    command = [sys.executable, "-m", "pip", "install", "--disable-pip-version-check",
               "--no-cache-dir", "--no-deps", "--no-build-isolation", "--target", str(target)]
    with (root / "bootstrap_pip.log").open("x") as log:
        subprocess.run(command + SMALL_DEPENDENCIES, stdout=log, stderr=subprocess.STDOUT, check=True)
    write_new(root / "bootstrap_completion.json", dict(
        status="CODE_READY_NO_MODEL_DOWNLOAD", seconds=time.monotonic() - started,
        sources=receipts, dependencies=SMALL_DEPENDENCIES, global_environment_modified=False,
    ))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # The caller saves this trace; do not erase partials or automatically retry.
        traceback.print_exc()
        raise
