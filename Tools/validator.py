#!/usr/bin/env python3
"""Validate translation YAML file: structure, completeness, and variable consistency."""

import sys
import os
import re
from pathlib import Path
from ruamel.yaml import YAML


# Patterns for variable placeholders
CURLY_VAR_RE = re.compile(r"\{[^}]+\}")
PRINTF_VAR_RE = re.compile(r"%\d+\$[a-z]")


def extract_variables(text: str) -> tuple:
    """Extract {var} and %N$type placeholders from a string."""
    if not isinstance(text, str):
        return set(), set()
    curly = set(CURLY_VAR_RE.findall(text))
    printf = set(PRINTF_VAR_RE.findall(text))
    return curly, printf


def validate_file(input_path: str, target_lang: str = None, check_vars: bool = True) -> int:
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.allow_duplicate_keys = True
    yaml.width = 4096

    # First pass: read raw lines for line number reporting
    with open(input_path, "r", encoding="utf-8") as f:
        raw_lines = f.readlines()

    # Build line number index: key path -> line number
    # YAML uses 2-space indentation: Sections(0) > SectionName(2) > Key(4) > Lang(6)
    line_index = {}
    current_section = None
    current_key = None
    for i, line in enumerate(raw_lines, 1):
        stripped = line.rstrip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        content = stripped.strip()

        if indent == 2 and ":" in content and content != "Sections:":
            current_section = content.split(":")[0].strip()
            current_key = None
        elif indent == 4 and ":" in content and current_section:
            current_key = content.split(":")[0].strip()
        elif indent == 6 and ":" in content and current_section and current_key:
            lang_code = content.split(":")[0].strip()
            line_index[(current_section, current_key, lang_code)] = i

    # Parse YAML
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            data = yaml.load(f)
    except Exception as e:
        print(f"ERROR: YAML parse error in {input_path}: {e}", file=sys.stderr)
        return 1

    if not data or "Sections" not in data:
        print(f"ERROR: No 'Sections' key found in {input_path}", file=sys.stderr)
        return 1

    errors = []
    warnings = []

    sections = data["Sections"]
    for section_name, keys in sections.items():
        if keys is None:
            continue
        if not isinstance(keys, dict):
            errors.append(f"ERROR: Section '{section_name}' is not a mapping")
            continue

        for key_name, langs in keys.items():
            if langs is None or not isinstance(langs, dict):
                errors.append(f"ERROR: Key '{section_name}.{key_name}' is not a mapping")
                continue

            # Check structure: all values under key should be language codes
            for lang_code, value in langs.items():
                if isinstance(value, dict):
                    line_num = line_index.get((section_name, key_name, lang_code), "?")
                    errors.append(
                        f"ERROR line {line_num}: Key '{section_name}.{key_name}.{lang_code}' "
                        f"has nested mapping — likely indentation error"
                    )

            # Check target language presence
            if target_lang:
                if "en" in langs and target_lang not in langs:
                    line_num = line_index.get((section_name, key_name, "en"), "?")
                    warnings.append(
                        f"WARN  line {line_num}: Key '{section_name}.{key_name}' — "
                        f"language '{target_lang}' not found"
                    )

            # Check variable consistency
            if check_vars and target_lang and "en" in langs and target_lang in langs:
                en_text = str(langs["en"])
                target_text = str(langs[target_lang])

                en_curly, en_printf = extract_variables(en_text)
                tgt_curly, tgt_printf = extract_variables(target_text)

                line_num = line_index.get((section_name, key_name, target_lang), "?")

                # Check {var} placeholders
                if en_curly != tgt_curly:
                    missing = en_curly - tgt_curly
                    extra = tgt_curly - en_curly
                    parts = []
                    if missing:
                        parts.append(f"missing {missing}")
                    if extra:
                        parts.append(f"extra {extra}")
                    errors.append(
                        f"ERROR line {line_num}: Key '{section_name}.{key_name}' — "
                        f"variable mismatch in '{target_lang}': {', '.join(parts)}"
                    )

                # Check %N$type placeholders
                if en_printf != tgt_printf:
                    missing = en_printf - tgt_printf
                    extra = tgt_printf - en_printf
                    parts = []
                    if missing:
                        parts.append(f"missing {missing}")
                    if extra:
                        parts.append(f"extra {extra}")
                    errors.append(
                        f"ERROR line {line_num}: Key '{section_name}.{key_name}' — "
                        f"printf placeholder mismatch in '{target_lang}': {', '.join(parts)}"
                    )

    # Output results
    for w in warnings:
        print(w)
    for e in errors:
        print(e)

    total_issues = len(errors)
    if total_issues == 0:
        print(f"OK: {input_path}" + (f" [{target_lang}]" if target_lang else ""))
        return 0
    else:
        print(f"\n{total_issues} error(s), {len(warnings)} warning(s) found")
        return 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: validator.py <input.yaml> [target_lang]", file=sys.stderr)
        sys.exit(1)

    input_file = sys.argv[1]
    lang = sys.argv[2] if len(sys.argv) > 2 else None

    if not os.path.exists(input_file):
        print(f"ERROR: File not found: {input_file}", file=sys.stderr)
        sys.exit(1)

    exit_code = validate_file(input_file, lang)
    sys.exit(exit_code)
