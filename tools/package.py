"""Build deterministic content and combined native Horizon packages."""
from pathlib import Path
import hashlib
import json
import tomllib
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def archive(path, entries):
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as output:
        for name, data in sorted(entries.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            output.writestr(info, data)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    print(f"{path.name}  {path.stat().st_size} bytes  SHA256 {digest}")
    return f"{digest}  {path.name}\n"


def main():
    content = ROOT / "content"
    manifest = tomllib.loads((content / "horizon-mod.toml").read_text())
    entries = {"horizon-mod.toml": (content / "horizon-mod.toml").read_bytes()}
    for directory in ("assets", "data"):
        for file in (content / directory).rglob("*"):
            if file.is_file():
                entries[file.relative_to(content).as_posix()] = file.read_bytes()
    output = ROOT / "dist"
    output.mkdir(exist_ok=True)
    stem = f"{manifest['id']}-{manifest['version']}"
    checksums = archive(output / f"{stem}-content.hmod", entries)
    bundles = list((ROOT / "native").glob("mixins/*/horizon-mixin.toml"))
    if len(bundles) != 1:
        raise SystemExit("Expected one native/mixins/*/horizon-mixin.toml")
    bundle = bundles[0].parent
    native = tomllib.loads(bundles[0].read_text())
    if native["mod"]["id"] != manifest["id"]:
        raise SystemExit("Native and content IDs must match")
    if native["mod"]["version"] != manifest["version"]:
        raise SystemExit("Native and content versions must match")
    native_manifest = {
        "schema": 1,
        "id": manifest["id"],
        "version": manifest["version"],
        "game": "26.3",
        "horizon": native["compatibility"]["horizon_revision"],
        "mixins": "5a64af938ec86b00d53d16a408aabc0038fb3e57",
    }
    entries["horizon-native.json"] = json.dumps(native_manifest, indent=2).encode()
    for file in bundle.rglob("*"):
        relative = file.relative_to(bundle)
        if file.is_file() and "target" not in relative.parts and file.suffix in (".rs", ".toml"):
            entries[f"mixins/{bundle.name}/{relative.as_posix()}"] = file.read_bytes()
    checksums += archive(output / f"{stem}.hmod", entries)
    (output / "SHA256SUMS").write_text(checksums, encoding="utf-8")


if __name__ == "__main__":
    main()
