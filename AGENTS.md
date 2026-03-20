# AGENTS.md

## Project Overview

Translation/localization repository for a carsharing/scooter-sharing platform. Contains YAML files with UI strings for multiple platforms, and a C# validator for CI.

## Supported Languages

`en` (English), `ru` (Russian), `it` (Italian), `cs` (Czech), `ka`/`ge` (Georgian), `uk` (Ukrainian), `kk` (Kazakh)

## YAML File Structure

All translation files follow this format:

```yaml
Sections:
  SectionName:
    key.identifier:
      en: English text
      ru: Русский текст
```

Translation files by platform:
- **frontend.yaml** — admin/profile web frontend (largest file)
- **server.yaml** — server-side messages (emails, errors, payments)
- **android.yaml** — Android app
- **ios.yaml** — iOS app
- **app.yaml** — shared app strings
- **sign-up-frontend.yaml** — registration page
- **b2bfrontend.yaml** — B2B interface

Not all languages are present for every key. `en` and `ru` are the primary languages present on most keys.

## Validation

YAML syntax is validated via a C# project (`YamlValidator/`) using YamlDotNet on .NET 6.

```bash
# Run validator locally
cd YamlValidator && dotnet run

# Or build and run
dotnet build -c Release YamlValidator/YamlValidator.csproj
dotnet run --project YamlValidator
```

CI runs this automatically on every push/PR via `.github/workflows/validate-yaml.yml`.

## Working with Translations

- When adding a new language, add the language code (e.g., `it:`) with the value after the `en:` line for each key. The value must be a proper translation from English to the target language, not a copy of the English text
- When adding a new translation key, include at minimum `en` and `ru` values
- Values can be unquoted or double-quoted; preserve the style used by neighboring keys
- Key naming uses dot-notation (e.g., `cars.models.DisplayDiscount`)

## Translation Toolkit (`Tools/`)

Python-based pipeline to minimize context window usage when translating YAML files. **Always use `python3` (not `python`) to run scripts.** Install dependencies: `pip3 install -r Tools/requirements.txt`

### When asked to add a language to a YAML file

Example prompt: "добавь итальянский язык в файл server.yaml"

Follow this pipeline strictly:

1. **Extract** source language:
   ```bash
   python3 Tools/extractor.py <file>.yaml en
   ```
   Output: `./tmp/<file>/en.yaml`

2. **Split** into chunks:
   ```bash
   python3 Tools/splitter.py ./tmp/<file>/en.yaml 20
   ```
   Output: `./tmp/<file>/en/1.yaml, 2.yaml, ...`

3. **Translate** each chunk (LLM does this directly):
   - Read each chunk file from `./tmp/<file>/en/`
   - Translate all values from `en` to the target language
   - **MUST preserve**: YAML structure, keys, variables (`{var}`, `%N$type`), HTML tags, quoting style
   - Write translated chunk to `./tmp/<file>/<target_lang>/N.yaml` (replace `en:` keys with `<target_lang>:` keys)
   - Process one chunk at a time to keep context window small

4. **Insert** translations back:
   ```bash
   python3 Tools/inserter.py ./tmp/<file>/<target_lang>/ <file>.yaml
   ```

5. **Validate** the result:
   ```bash
   python3 Tools/validator.py <file>.yaml <target_lang>
   ```

6. If validator reports errors — fix them directly in the YAML file

### When asked to create a separate translation file

Example prompt: "создай файл итальянских переводов на основе ios.yaml"

Same pipeline, but step 4 outputs to a **new file** instead of merging into the original:

1. **Extract**: `python3 Tools/extractor.py <file>.yaml en`
2. **Split**: `python3 Tools/splitter.py ./tmp/<file>/en.yaml 20`
3. **Translate** each chunk (same as above)
4. **Create** separate file (inserter auto-creates if target doesn't exist):
   ```bash
   python3 Tools/inserter.py ./tmp/<file>/<target_lang>/ <file>-<target_lang>.yaml
   ```
5. **Validate**: `python3 Tools/validator.py <file>-<target_lang>.yaml <target_lang>`
6. Fix any validation errors

### Tool reference

| Tool | Purpose | Usage |
|------|---------|-------|
| `extractor.py` | Extract single language from YAML | `extractor.py <file> [lang=en]` |
| `splitter.py` | Split YAML into chunks | `splitter.py <file> [chunk_kb=20]` |
| `inserter.py` | Merge translations into existing file or create new | `inserter.py <source_dir_or_file> <target.yaml>` |
| `validator.py` | Validate structure and variables | `validator.py <file> [target_lang]` |
