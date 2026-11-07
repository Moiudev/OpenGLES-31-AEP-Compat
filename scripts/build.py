#!/usr/bin/env python3
"""为 Magisk 模块构建 ZIP。

项目结构约定：
  项目根目录/
    module/        需要打进 ZIP 的模块文件
    scripts/build.py
    release/       自动生成的 ZIP

ZIP 内部会直接包含 module/ 的内容，不会额外嵌套 module 文件夹。
"""

from __future__ import annotations

import re
import stat
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODULE_DIR = ROOT / "module"
RELEASE_DIR = ROOT / "release"


def fail(message: str) -> None:
    print(f"[错误] {message}", file=sys.stderr)
    raise SystemExit(1)


def read_module_prop(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except OSError as exc:
        fail(f"无法读取 module.prop：{exc}")

    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def validate_module() -> tuple[dict[str, str], list[Path]]:
    if not MODULE_DIR.is_dir():
        fail(f"找不到模块源码目录：{MODULE_DIR}\n请在项目根目录创建 module 文件夹。")

    required_files = [
        MODULE_DIR / "module.prop",
        MODULE_DIR / "customize.sh",
        MODULE_DIR / "system.prop",
        MODULE_DIR / "system/vendor/etc/permissions/android.hardware.opengles.aep.xml",
    ]
    for path in required_files:
        if not path.is_file():
            fail(f"缺少必要文件：{path.relative_to(ROOT).as_posix()}")

    props = read_module_prop(MODULE_DIR / "module.prop")
    for key in ("id", "name", "version", "versionCode"):
        if not props.get(key):
            fail(f"module.prop 缺少必要字段：{key}")

    if not re.fullmatch(r"[A-Za-z0-9._-]+", props["id"]):
        fail("module.prop 中的 id 只能包含英文字母、数字、点、下划线和连字符。")

    # 若模块包含 Recovery 安装入口，则检查其必要文件。
    meta = MODULE_DIR / "META-INF/com/google/android"
    update_binary = meta / "update-binary"
    updater_script = meta / "updater-script"
    if meta.exists():
        if not update_binary.is_file() or not updater_script.is_file():
            fail("META-INF 安装入口不完整，必须同时包含 update-binary 和 updater-script。")
        updater_text = updater_script.read_text(encoding="utf-8-sig").strip()
        if updater_text != "#MAGISK":
            fail("META-INF/com/google/android/updater-script 的内容必须只有 #MAGISK。")
        first_line = update_binary.open("rb").readline().decode("utf-8", errors="replace").strip()
        if not first_line.startswith("#!"):
            fail("update-binary 缺少有效的 Shell shebang。")

    xml_path = required_files[-1]
    try:
        ET.parse(xml_path)
    except ET.ParseError as exc:
        fail(f"AEP XML 格式错误：{exc}")

    files = sorted(p for p in MODULE_DIR.rglob("*") if p.is_file())
    if not files:
        fail("模块目录中没有可打包的文件。")

    # 不允许符号链接，避免打包时意外包含模块目录之外的内容。
    for path in files:
        if path.is_symlink():
            fail(f"暂不支持打包符号链接：{path.relative_to(ROOT).as_posix()}")

    return props, files


def make_zip(props: dict[str, str], files: list[Path]) -> Path:
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)
    id = props["id"]
    version = props["version"]
    zip_name = f"{id}_v{version}.zip"
    output_path = RELEASE_DIR / zip_name

    # 所有文件路径都相对于 module/，确保 module.prop 位于 ZIP 根目录。
    with zipfile.ZipFile(output_path, "w") as archive:
        for source in files:
            relative_name = source.relative_to(MODULE_DIR).as_posix()
            is_recovery_installer = relative_name == "META-INF/com/google/android/update-binary"

            # ZIP 使用 Unix 文件属性：普通文件 0644，Recovery update-binary 0755。
            permissions = 0o755 if is_recovery_installer else 0o644
            unix_mode = stat.S_IFREG | permissions

            info = zipfile.ZipInfo(relative_name)
            info.create_system = 3  # Unix
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = unix_mode << 16

            try:
                data = source.read_bytes()
            except OSError as exc:
                fail(f"读取文件失败 {relative_name}：{exc}")
            archive.writestr(info, data)

    # 构建后复核 ZIP 完整性、根目录结构及权限记录。
    try:
        with zipfile.ZipFile(output_path, "r") as archive:
            bad_file = archive.testzip()
            if bad_file:
                fail(f"ZIP 完整性检查失败：{bad_file}")

            names = set(archive.namelist())
            if "module.prop" not in names:
                fail("ZIP 根目录中没有 module.prop，打包层级不正确。")

            for name in names:
                if name.startswith("module/"):
                    fail("ZIP 中出现多余的 module/ 顶层目录。")

            if "META-INF/com/google/android/update-binary" in names:
                entry = archive.getinfo("META-INF/com/google/android/update-binary")
                mode = (entry.external_attr >> 16) & 0o777
                if mode != 0o755:
                    fail(f"update-binary 权限不正确：{mode:o}，预期 755。")
    except zipfile.BadZipFile as exc:
        fail(f"生成的 ZIP 无法读取：{exc}")

    return output_path


def main() -> None:
    print("========================================")
    print(" OpenGL ES 3.1 扩展兼容增强模块")
    print("========================================")

    props, files = validate_module()
    output = make_zip(props, files)

    print(f"[通过] 模块：{props['name']}")
    print(f"[通过] 版本：{props['version']} (versionCode={props['versionCode']})")
    print(f"[通过] 文件数量：{len(files)}")
    print("[通过] ZIP 完整性与根目录结构")
    print(f"[完成] 输出文件：{output}")


if __name__ == "__main__":
    main()
