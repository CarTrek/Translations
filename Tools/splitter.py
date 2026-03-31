#!/usr/bin/env python3
"""Split a translation YAML file into chunks of a given size."""

import sys
import os
from io import StringIO
from pathlib import Path
from ruamel.yaml import YAML


def estimate_size(yaml_instance, data) -> int:
    """Estimate serialized YAML size in bytes."""
    buf = StringIO()
    yaml_instance.dump(data, buf)
    return len(buf.getvalue().encode("utf-8"))


def build_chunk(section_name: str, keys: dict, yaml_instance) -> dict:
    """Build a valid YAML document with the given keys under a section."""
    from ruamel.yaml.comments import CommentedMap
    doc = CommentedMap()
    sections = CommentedMap()
    section = CommentedMap()
    for k, v in keys.items():
        section[k] = v
    sections[section_name] = section
    doc["Sections"] = sections
    return doc


def split_file(input_path: str, chunk_size_kb: int = 20) -> str:
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.allow_duplicate_keys = True
    yaml.width = 4096

    chunk_size_bytes = chunk_size_kb * 1024

    with open(input_path, "r", encoding="utf-8") as f:
        data = yaml.load(f)

    if "Sections" not in data:
        print(f"ERROR: No 'Sections' key found in {input_path}", file=sys.stderr)
        sys.exit(1)

    # Build output dir: if input is ./tmp/server/en.yaml → ./tmp/server/en/
    input_p = Path(input_path)
    output_dir = input_p.parent / input_p.stem
    output_dir.mkdir(parents=True, exist_ok=True)

    sections = data["Sections"]
    chunk_num = 0
    current_keys = {}
    current_section = None

    def flush_chunk(sec_name, keys):
        nonlocal chunk_num
        if not keys:
            return
        chunk_num += 1
        chunk_data = build_chunk(sec_name, keys, yaml)
        chunk_path = output_dir / f"{chunk_num}.yaml"
        with open(chunk_path, "w", encoding="utf-8") as f:
            yaml.dump(chunk_data, f)

    for section_name, keys in sections.items():
        if keys is None:
            continue
        current_section = section_name
        current_keys = {}

        for key_name, langs in keys.items():
            # Tentatively add this key
            current_keys[key_name] = langs

            # Check current chunk size
            chunk_data = build_chunk(section_name, current_keys, yaml)
            size = estimate_size(yaml, chunk_data)

            if size > chunk_size_bytes and len(current_keys) > 1:
                # Remove last key and flush
                last_val = current_keys.pop(key_name)
                flush_chunk(section_name, current_keys)
                current_keys = {key_name: last_val}

        # Flush remaining keys for this section
        flush_chunk(section_name, current_keys)
        current_keys = {}

    print(f"Split into {chunk_num} chunks → {output_dir}/")
    return str(output_dir)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: splitter.py <input.yaml> [chunk_size_kb=20]", file=sys.stderr)
        sys.exit(1)

    input_file = sys.argv[1]
    size_kb = int(sys.argv[2]) if len(sys.argv) > 2 else 20

    if not os.path.exists(input_file):
        print(f"ERROR: File not found: {input_file}", file=sys.stderr)
        sys.exit(1)

    split_file(input_file, size_kb)
