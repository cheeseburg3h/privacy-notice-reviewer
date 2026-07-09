from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from app.config import DATA_DIR, OUTPUTS_DIR, PROCESSED_DIR


def delete_client_data(company_slug: str, dry_run: bool = True) -> list[Path]:
    targets = [
        DATA_DIR / "client_inputs" / company_slug,
        OUTPUTS_DIR / company_slug,
    ]
    targets.extend(PROCESSED_DIR.glob(f"{company_slug}*"))
    deleted: list[Path] = []
    for target in targets:
        if not target.exists():
            continue
        deleted.append(target)
        if dry_run:
            continue
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
    return deleted


def main() -> None:
    parser = argparse.ArgumentParser(description="Delete client-specific inputs, processed chunks, and outputs.")
    parser.add_argument("--company", required=True)
    parser.add_argument("--confirm", action="store_true", help="Actually delete files. Without this flag, dry-run only.")
    args = parser.parse_args()
    targets = delete_client_data(args.company, dry_run=not args.confirm)
    mode = "Would delete" if not args.confirm else "Deleted"
    for target in targets:
        print(f"{mode}: {target}")
    if not targets:
        print("No client-specific files found.")


if __name__ == "__main__":
    main()

