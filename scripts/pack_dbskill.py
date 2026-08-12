"""把 dbskill-2.18.17 下所有 skill 目录打包成 Trae Solo 可上传的 zip。

每个 skill 目录内含 SKILL.md（根级），zip 解压后根级直接是 SKILL.md 文件。
输出到 g:/ai-daily/dbskill-zips/<skill-name>.zip
"""
import os
import zipfile
from pathlib import Path

ROOT = Path(r"g:\ai-daily\dbskill-2.18.17")
OUT = Path(r"g:\ai-daily\dbskill-zips")


def find_skill_dirs(root: Path):
    """找到所有含 SKILL.md 的目录（排除已含 SKILL.md 的嵌套子目录，避免重复）"""
    skill_dirs = []
    for dirpath, dirnames, filenames in os.walk(root):
        if "SKILL.md" in filenames:
            skill_dirs.append(Path(dirpath))
            # 该目录下已找到 skill，不再下钻（dbs-content-system 的 scaffold 可能含 SKILL.md? 无）
    return skill_dirs


def make_zip(skill_dir: Path, out_dir: Path) -> Path:
    """把 skill 目录内容压缩为 zip，zip 根级是 SKILL.md"""
    skill_name = skill_dir.name
    zip_path = out_dir / f"{skill_name}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in sorted(skill_dir.rglob("*")):
            if file.is_file():
                # 相对 skill 目录的路径作为 zip 内路径（根级即 SKILL.md）
                arcname = file.relative_to(skill_dir).as_posix()
                zf.write(file, arcname)
    return zip_path


def main():
    skill_dirs = find_skill_dirs(ROOT)
    print(f"发现 {len(skill_dirs)} 个 skill 目录")
    OUT.mkdir(parents=True, exist_ok=True)

    for skill_dir in skill_dirs:
        # 跳过已存在的输出 zip（避免重复打包）
        if OUT.name in skill_dir.parts:
            continue
        zip_path = make_zip(skill_dir, OUT)
        print(f"  ✅ {skill_dir.name} -> {zip_path.name}")

    print(f"\n完成。共 {len([p for p in OUT.glob('*.zip')])} 个 zip 已生成到 {OUT}")


if __name__ == "__main__":
    main()
