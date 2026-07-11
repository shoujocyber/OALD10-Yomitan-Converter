# OALD10-Yomitan-Converter

A Python converter that parses the **Oxford Advanced Learner's Dictionary, 10th Edition (EN-ZH)** MDX data and rebuilds it as a native Yomitan structured-content dictionary.

The project focuses on three things: clean Yomitan rendering, predictable Anki export, and an auditable conversion pipeline. Dictionary data is not included in this repository.

## 🌟 Features (V3.1)

- **Extractor -> IR -> Renderer -> Packager architecture**: MDX HTML is normalized into an intermediate representation before any Yomitan JSON is rendered.
- **Full source-to-IR integrity audit**: counts entries, senses, definitions, translations, retained examples, topics, sense-level Oxford/CEFR labels, usage notes, panels, panel payloads, and cross-references. Sense-level mismatches stop the build instead of being silently ignored.
- **Complete known-panel coverage**: handles all 18 panel types found in the current source, including Word Origin, Collocations, Extra Examples, Homophones, Wordfinder, Word Family, Language Bank, Which Word, Grammar, Vocabulary, Verb Forms, and Synonyms.
- **Cleaner OALD extraction**: preserves shortcuts, grammar/topic labels, entry- and sense-level Oxford3000/Oxford5000 + CEFR labels, variants, construction patterns, definition links, multiple example lists, usage notes, phrasal verbs, idioms, and nested rich text.
- **Conservative visual hierarchy**: stable sense numbering, readable bilingual/monolingual definitions, aligned examples, compact semantic labels, and level-aware collapsible panels.
- **Anki-safe structured content**: normal builds contain no unsupported inline `style` fields or debug-only `open` fields. Rendering uses semantic classes defined in the bundled stylesheet.
- **Source hygiene**: filters 37 internal `oalecd_ref_*` reference pages and source-empty entry placeholders so they cannot become fake or blank dictionary results.
- **Strict package validation**: checks required files, JSON rows, empty definitions, blank headers, leaked internal markers, undefined tags, undefined CSS classes, mode-specific language policy, and redirects to missing terms. Immersion rejects Chinese body content; Global rejects both Chinese-language nodes and untagged CJK text.
- **Release-grade metadata**: separates the converter version, dictionary build revision, and source-data revision; publishes project, release, and source-attribution links; and declares source/target languages for each edition.
- **Three output editions**: Standard Bilingual, Chinese-assisted Immersion, and English-only Global.
- **Focused debug builds**: `--test-words` builds a small readable package without weakening the same extraction and ZIP validation rules.

## 📸 Screenshot

<img alt="OALD 10 rendered in Yomitan" src="https://github.com/user-attachments/assets/da0fe523-5870-4ce6-8929-fc222f0a04b7" />

## 📋 Requirements

- Python 3.10 or newer
- `beautifulsoup4`
- `tqdm`
- `mdict-utils` if the MDX still needs to be extracted

Using a virtual environment is recommended.

### Windows

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install beautifulsoup4 tqdm mdict-utils
```

### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
pip install beautifulsoup4 tqdm mdict-utils
```

## 🛠️ Obtain and Extract the Source

This converter targets the OALD 10 data shared by xingxingla on the FreeMdict Forum:

- [牛津高阶双解第10版完美版重生版（OALDPEX）](https://forum.freemdict.com/t/topic/43710)

Extract the MDX with `mdict-utils`:

```bash
mdict -x oaldpe.mdx -d ./
```

Pass the actual extracted text filename to `-i`. It does not need to be renamed to `oaldpe.txt`.

## Build Dictionaries

Use a separate output directory for each edition. This is required when builds are run in parallel and also keeps the generated files easy to identify.

### Standard Bilingual

English definitions, Chinese translations, and Chinese UI labels:

```powershell
python main.py -i oaldpe-20260711.mdx.txt -o build\bilingual -m bilingual -u zh
```

Output: `OALD10_Yomitan_V3.1.0.zip`

### Immersion

English definitions, examples, notes, and panel bodies with Chinese-assisted navigation and compact metadata. Source translations are retained for shortcuts, variants, register/region labels, and usage restrictions; a closed glossary supplies common grammar labels such as `countable 可数` and `intransitive 不及物`:

```powershell
python main.py -i oaldpe-20260711.mdx.txt -o build\immersion -m mono -u zh
```

Output: `OALD10_Yomitan_V3.1.0_Immersion.zip`

### Global

English-only dictionary content, metadata, and UI labels:

```powershell
python main.py -i oaldpe-20260711.mdx.txt -o build\global -m mono -u en
```

Output: `OALD10_Yomitan_V3.1.0_Global.zip`

Full builds are CPU-intensive. Sequential builds are the conservative choice; parallel builds should use different output directories and enough available memory.

The dictionary revision shown by Yomitan defaults to the date on which the package is built. The source-data revision is inferred separately from an eight-digit date in the input filename and written to the description. For example, a package rebuilt on 2026-07-15 from `oaldpe-20260711.mdx.txt` displays `rev.2026.07.15`, while its description records source data `2026.07.11` and converter `v3.1.0`.

For a coordinated three-edition release, pass the same explicit revision to all three commands (for example, `--revision 2026.07.15`). This keeps the release reproducible and avoids different dates if a long build crosses midnight.

## Debug Workflow

Build only selected words:

```powershell
python main.py -i oaldpe-20260711.mdx.txt -o build\debug --test-words "read,judgement,attention,outstay"
```

Debug builds write indented JSON, keep `term_bank_*.json` by default, and open details panels for visual inspection. Add `--closed-panels` to reproduce normal release behavior.

## Arguments

| Argument | Description |
| --- | --- |
| `-i`, `--input` | Required path to the extracted MDX text file. |
| `-o`, `--output` | Output directory. Default: `./yomitan_v3`. |
| `-m`, `--mode` | `bilingual` (default) or `mono`. |
| `-u`, `--ui-lang` | `zh` (default) or `en` for UI labels and metadata. |
| `--revision` | Build revision displayed by Yomitan. Defaults to today's date in `YYYY.MM.DD` format. |
| `--debug` | Build the default debug word set and write readable JSON. |
| `--test-words` | Comma- or semicolon-separated words; implies `--debug`. Matching is case-insensitive. |
| `--open-panels` | Force details panels open. |
| `--closed-panels` | Keep details panels closed, including in debug builds. |
| `--keep-json` | Keep generated term-bank JSON after compression. |
| `--discard-json` | Remove term-bank JSON even in debug builds. |
| `--skip-validation` | Skip extraction and ZIP validation. Intended only for diagnosis, not release builds. |

Run `python main.py --help` for the current command-line help.

### Language Policy

The full Immersion build contains Chinese only in approved shortcut, grammar, variant, cross-reference, and panel-title nodes. Chinese definition, example, note, and panel-body nodes: `0`. The full Global build contains both `0` `lang=zh` nodes and `0` CJK text characters.

Each generated `index.json` includes the converter author, [GitHub project URL](https://github.com/shoujocyber/OALD10-Yomitan-Converter), [FreeMdict release page](https://forum.freemdict.com/t/topic/44052), OUP/source attribution with the [FreeMdict data thread](https://forum.freemdict.com/t/topic/43710), and ISO source/target language codes. Automatic-update metadata is intentionally omitted until stable `indexUrl` and `downloadUrl` endpoints exist.

The source also contains two genuinely empty sense placeholders (`cave` and `said`); they are reported and filtered rather than rendered as blank senses.

## Import and Update

Import the generated ZIP directly in Yomitan. Do not extract it first.

When upgrading, remove the old dictionary from Yomitan, import the new ZIP, and wait for indexing to finish before testing lookups. Anki card templates can override dictionary colors and fonts; V3.1 guarantees valid structured content and bundled class definitions, but cannot override every template's CSS policy.

## ⚖️ License

Licensed under the [GNU Affero General Public License v3.0](LICENSE).

## ⚠️ Disclaimer

This repository contains only the conversion script. It does not contain, distribute, or host Oxford dictionary data. Use the converter for personal educational purposes and respect the rights of Oxford University Press and the original data providers.
