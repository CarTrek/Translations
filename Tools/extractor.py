#!/usr/bin/env python3
"""Extract a single language from a translation YAML file."""

import sys
import os
from pathlib import Path
from copy import deepcopy
from ruamel.yaml import YAML


def extract_language(input_path: str, lang: str = "en") -> str:
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.allow_duplicate_keys = True
    yaml.width = 4096  # prevent line wrapping

    with open(input_path, "r", encoding="utf-8") as f:
        data = yaml.load(f)

    if "Sections" not in data:
        print(f"ERROR: No 'Sections' key found in {input_path}", file=sys.stderr)
        sys.exit(1)

    sections = data["Sections"]
    for section_name, keys in sections.items():
        if keys is None:
            continue
        keys_to_delete = []
        for key_name, langs in list(keys.items()):
            if langs is None or not isinstance(langs, dict):
                keys_to_delete.append(key_name)
                continue
            if lang not in langs:
                keys_to_delete.append(key_name)
                continue
            # Keep only the target language
            lang_keys_to_remove = [l for l in langs if l != lang]
            for l in lang_keys_to_remove:
                del langs[l]
        for k in keys_to_delete:
            del keys[k]

    # Build output path: ./tmp/{filename}/{lang}.yaml
    filename = Path(input_path).stem
    output_dir = Path("tmp") / filename
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{lang}.yaml"

    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f)

    print(f"Extracted '{lang}' → {output_path}")
    return str(output_path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: extractor.py <input.yaml> [lang=en]", file=sys.stderr)
        sys.exit(1)

    input_file = sys.argv[1]
    language = sys.argv[2] if len(sys.argv) > 2 else "en"

    if not os.path.exists(input_file):
        print(f"ERROR: File not found: {input_file}", file=sys.stderr)
        sys.exit(1)

    extract_language(input_file, language)
