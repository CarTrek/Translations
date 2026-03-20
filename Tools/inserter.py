#!/usr/bin/env python3
"""Insert translated YAML chunks back into the original translation file."""

import sys
import os
from pathlib import Path
from ruamel.yaml import YAML


def load_chunks(source_path: str) -> list:
    """Load YAML data from a directory of chunks or a single file."""
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.allow_duplicate_keys = True
    yaml.width = 4096

    source = Path(source_path)
    chunks = []

    if source.is_dir():
        # Sort numerically by filename
        files = sorted(source.glob("*.yaml"), key=lambda f: int(f.stem) if f.stem.isdigit() else f.stem)
        for f in files:
            with open(f, "r", encoding="utf-8") as fh:
                data = yaml.load(fh)
                if data:
                    chunks.append(data)
    elif source.is_file():
        with open(source, "r", encoding="utf-8") as fh:
            data = yaml.load(fh)
            if data:
                chunks.append(data)
    else:
        print(f"ERROR: Path not found: {source_path}", file=sys.stderr)
        sys.exit(1)

    return chunks


def insert_translations(source_path: str, target_path: str):
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.allow_duplicate_keys = True
    yaml.width = 4096

    # Load target file
    with open(target_path, "r", encoding="utf-8") as f:
        target_data = yaml.load(f)

    if "Sections" not in target_data:
        print(f"ERROR: No 'Sections' key found in {target_path}", file=sys.stderr)
        sys.exit(1)

    # Load source chunks
    chunks = load_chunks(source_path)

    # Merge translations
    inserted = 0
    for chunk in chunks:
        if "Sections" not in chunk:
            continue
        for section_name, keys in chunk["Sections"].items():
            if keys is None:
                continue
            if section_name not in target_data["Sections"]:
                print(f"WARN: Section '{section_name}' not found in target, skipping", file=sys.stderr)
                continue
            target_section = target_data["Sections"][section_name]
            for key_name, langs in keys.items():
                if langs is None or not isinstance(langs, dict):
                    continue
                if key_name not in target_section:
                    print(f"WARN: Key '{section_name}.{key_name}' not found in target, skipping", file=sys.stderr)
                    continue
                target_langs = target_section[key_name]
                for lang, value in langs.items():
                    target_langs[lang] = value
                    inserted += 1

    # Write back
    with open(target_path, "w", encoding="utf-8") as f:
        yaml.dump(target_data, f)

    print(f"Inserted {inserted} translations into {target_path}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: inserter.py <source_dir_or_file> <target.yaml>", file=sys.stderr)
        sys.exit(1)

    source = sys.argv[1]
    target = sys.argv[2]

    if not os.path.exists(target):
        print(f"ERROR: Target file not found: {target}", file=sys.stderr)
        sys.exit(1)

    insert_translations(source, target)
