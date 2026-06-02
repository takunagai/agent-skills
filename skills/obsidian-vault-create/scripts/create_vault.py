#!/usr/bin/env python3
import argparse
import datetime as dt
import re
import shutil
from pathlib import Path


DEFAULT_BASE_DIR = Path.home() / "Documents"
FOLDER_INBOX = "00-Inbox"
FOLDER_NOTES = "01-Notes"
FOLDER_PROJECTS = "02-Projects"
FOLDER_RESOURCES = "03-Resources"
FOLDER_TEMPLATES = "04-Templates"
FOLDER_ASSETS = "05-Assets"
FOLDER_DAILY = "06-Daily"
FOLDER_ARCHIVE = "99-Archive"
DEFAULT_FOLDERS = [
    FOLDER_INBOX,
    FOLDER_NOTES,
    FOLDER_PROJECTS,
    FOLDER_RESOURCES,
    FOLDER_TEMPLATES,
    FOLDER_ASSETS,
    FOLDER_DAILY,
    FOLDER_ARCHIVE,
]


def sanitize_project(name: str) -> str:
    name = name.strip()
    name = re.sub(r'[\\/:*?"<>|]', "-", name)
    name = re.sub(r"\s+", "-", name)
    name = re.sub(r"-{2,}", "-", name)
    return name.strip("-")


def resolve_config_source(path: str | None) -> Path | None:
    if not path:
        return None
    p = Path(path).expanduser()
    if p.is_dir() and p.name == ".obsidian":
        return p
    if p.is_dir() and (p / ".obsidian").is_dir():
        return p / ".obsidian"
    raise SystemExit(
        "config-source must be a vault root containing .obsidian or a .obsidian directory"
    )


def parse_date(value: str | None) -> str:
    if not value:
        return dt.date.today().isoformat()
    try:
        parsed = dt.date.fromisoformat(value)
    except ValueError as exc:
        raise SystemExit("date must be YYYY-MM-DD") from exc
    return parsed.isoformat()


def write_daily_template(vault_path: Path) -> None:
    template_path = vault_path / FOLDER_TEMPLATES / "Daily.md"
    if template_path.exists():
        return
    template_path.write_text(
        "# {{date:YYYY-MM-DD}}\n\n"
        "## Tasks\n"
        "- [ ] \n",
        encoding="utf-8",
    )


def write_readme(vault_path: Path, date_str: str, project: str) -> None:
    readme_path = vault_path / "README.md"
    if readme_path.exists():
        return
    readme_path.write_text(
        "# Obsidian Vault\n\n"
        f"- Project: {project}\n"
        f"- Created: {date_str}\n"
        f"- Location: {vault_path}\n",
        encoding="utf-8",
    )


def write_home(vault_path: Path) -> None:
    home_path = vault_path / "Home.md"
    if home_path.exists():
        return
    home_path.write_text(
        "# Home\n\n"
        "## Today\n"
        "- [ ] \n\n"
        "## Notes\n"
        "- \n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a new Obsidian vault with a standard layout."
    )
    parser.add_argument("--project", required=True, help="Project name for the vault")
    parser.add_argument(
        "--date", help="Vault date in YYYY-MM-DD format (default: today)"
    )
    parser.add_argument(
        "--base-dir",
        default=str(DEFAULT_BASE_DIR),
        help=f"Base directory (default: {DEFAULT_BASE_DIR})",
    )
    parser.add_argument(
        "--skip-daily",
        action="store_true",
        help="Skip creating Daily folder and a Templates/Daily.md template",
    )
    parser.add_argument(
        "--config-source",
        help="Path to a vault root or .obsidian directory to copy settings from",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show actions without creating files",
    )
    args = parser.parse_args()

    date_str = parse_date(args.date)
    project = sanitize_project(args.project)
    if not project:
        raise SystemExit("project name is empty after sanitization")

    vault_name = f"{date_str}-{project}"
    base_dir = Path(args.base_dir).expanduser()
    vault_path = base_dir / vault_name

    config_source = resolve_config_source(args.config_source)

    folders = list(DEFAULT_FOLDERS)
    if args.skip_daily:
        folders = [folder for folder in folders if folder != FOLDER_DAILY]

    if args.dry_run:
        print(f"Would create: {vault_path}")
        for folder in folders:
            print(f"Would create folder: {vault_path / folder}")
        if not args.skip_daily:
            print(
                f"Would write template: {vault_path / FOLDER_TEMPLATES / 'Daily.md'}"
            )
        print(f"Would write file: {vault_path / 'README.md'}")
        print(f"Would write file: {vault_path / 'Home.md'}")
        if config_source:
            print(f"Would copy settings: {config_source} -> {vault_path / '.obsidian'}")
        return

    if vault_path.exists():
        raise SystemExit(f"target already exists: {vault_path}")

    base_dir.mkdir(parents=True, exist_ok=True)
    vault_path.mkdir()

    for folder in folders:
        (vault_path / folder).mkdir(parents=True, exist_ok=False)

    write_readme(vault_path, date_str, project)
    write_home(vault_path)

    if not args.skip_daily:
        write_daily_template(vault_path)

    if config_source:
        shutil.copytree(config_source, vault_path / ".obsidian")

    print(f"Created vault: {vault_path}")


if __name__ == "__main__":
    main()
