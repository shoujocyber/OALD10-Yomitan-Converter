# OALD10-Yomitan-Converter (Dictionary Builder)

An advanced Python script to deeply parse, clean, and restructure the **Oxford Advanced Learner's Dictionary (10th Ed) EN-ZH** MDX data into a highly optimized, native Yomitan/Yomichan JSON dictionary.

## 🌟 Features (V3.0 核心特性)

Unlike raw MDX conversions (e.g., via PyGlossary) which result in cluttered HTML layouts and broken labels, this script uses a decoupled **Extractor -> IR -> Renderer -> Packager** pipeline designed specifically for this OALD source.

- **Structured-content first (原生结构化内容)**: Rebuilds entries as Yomitan structured content instead of dumping raw MDX HTML, so definitions, examples, labels, links, and collapsible panels render cleanly in Yomitan and Anki exports.
- **Cleaner OALD extraction (更稳的 OALD 抽取)**: Preserves headword labels, sense-level topic/grammar labels, variants, patterns, shortcuts, homophones, word origins, collocations, extra examples, word finder panels, and cross-references while avoiding common label leaks and fake bottom headings.
- **Anki-safe output (Anki 导入友好)**: Removes unsupported inline `style` fields and strips `open` fields from normal builds, preventing Yomitan import errors and messy Anki card output.
- **Bilingual/monolingual layout tuning (双语/单语独立排版)**: Uses separate CSS spacing for bilingual and monolingual examples, stable numbered sense headers, compact grammar pills, aligned example markers, and cleaner collapsible panels.
- **Debug workflow (调试工作流)**: `--debug` and `--test-words` create small readable test packages; debug panels open by default for quick visual inspection, while `--closed-panels` can force Anki-like closed output.
- **Built-in package validation (内置包体自检)**: After building, the script validates required Yomitan files, term bank counts, structured rows, redirects, unsupported keys, blank sense headers, and mode-specific CSS.
- **Internationalization (i18n 国际化)**: Supports bilingual EN-ZH and monolingual EN-EN content, with Chinese or English UI tag metadata.

---

## 📸 Screenshots (实际效果)

*(A clean layout, native Yomitan tag coloring, smart example sorting, and deep panel extraction.)*

**Clean Layout & Deep Restructuring (纯净排版与特种面板解析)**

<img alt="image" src="https://github.com/user-attachments/assets/b6e4e282-0092-4300-bd19-10fd3dfa0882" />


---

## 📋 Prerequisites (环境要求)

- **Python**: Version 3.10 or higher.
- **OS**: Windows, macOS, or Linux.

---

## 🛠️ How to Build (如何自己构建)

Because of copyright restrictions, **this repository DOES NOT contain the dictionary data**. You must build it yourself using the original MDX file.

### Step 1: Obtain the MDX (获取原始词典)
This script is strictly designed to parse the **OALD 10th Edition** shared by xingxingla on the Freemdict Forum.

🔗 **Source link**: [牛津高阶双解第10版完美版重生版（OALDPEX） - Freemdict Forum](https://forum.freemdict.com/t/topic/43710)
Please download the `oaldpe.mdx` file from the link above.

### Step 2: Set Up Virtual Environment (推荐配置虚拟环境)
It is highly recommended to use a virtual environment to avoid conflicts with your system packages. Open your terminal and run:

**For Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**For macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Unpack the MDX (解包MDX)
1. Install the required MDX extraction tool:
```bash
pip install mdict-utils
```
2. Extract the MDX file into a plain text file named `oaldpe.txt`:
```bash
mdict -x oaldpe.mdx -d ./
```
*(Ensure the output text file is renamed exactly to `oaldpe.txt` and placed in the same folder as `main.py`)*

### Step 4: Run the Parser (运行清洗与自动打包)

1. Install the HTML parsing and progress bar libraries:
```bash
pip install beautifulsoup4 tqdm
```

2. Run the conversion script using the command line:

**Bilingual Mode / Chinese Tags (英汉双解 + 中文标签释义)**:
```bash
python main.py -i path/to/your/oaldpe.txt
```

**Monolingual Mode / Chinese Tags (纯英沉浸 + 中文标签释义)**:
```bash
python main.py -i path/to/your/oaldpe.txt -m mono -u zh
```

**Monolingual Mode / English Tags (纯英国际 + 英文标签)**:
```bash
python main.py -i path/to/your/oaldpe.txt -m mono -u en
```

**Debug Build / Selected Words (调试小包)**:
```bash
python main.py -i path/to/your/oaldpe.txt --test-words read,judgement,attention
```

**Arguments Documentation**:
- `-i`, `--input`: Required. Path to the extracted MDX text file.
- `-o`, `--output`: Output folder path. Defaults to `./yomitan_v3`.
- `-m`, `--mode`: Dictionary content mode. Choose `bilingual` (default) or `mono`.
- `-u`, `--ui-lang`: Language for Yomitan tag names and metadata. Choose `zh` (default) or `en`.
- `--debug`: Build only the default debug word list and write readable indented JSON. Details panels are open by default in debug builds.
- `--test-words`: Comma-separated words for a small debug build. Passing this flag implies `--debug`.
- `--open-panels`: Force collapsible details panels to be open in the generated structured content.
- `--closed-panels`: Keep details panels closed even in debug builds.
- `--keep-json`: Keep generated `term_bank_*.json` files after creating the zip. Debug builds keep them by default.
- `--discard-json`: Remove generated `term_bank_*.json` files after creating the zip, even in debug builds.
- `--skip-validation`: Skip the built-in Yomitan zip validation step.

3. Wait for the magic to happen! The script will parse the data, generate the dictionaries, validate the generated Yomitan package, and automatically pack everything into a final zip file (e.g., `OALD10_Yomitan_V3.0.0.zip` or `OALD10_Yomitan_V3.0.0_Immersion.zip`).

4. **Import to Yomitan**: Open your Yomitan settings, go to Dictionaries, and import the newly generated `.zip` file directly. Done!

---

## ⚖️ License (开源协议)
This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0).
You are free to use, modify, and distribute this software, but any derivative works (including modifications or providing it as a network service) must strictly be open-sourced under the same license.

---

## ⚠️ Disclaimer (免责声明)
This repository ONLY contains the Python processing script. It does NOT contain, distribute, or host any copyrighted dictionary data (HTML/MDX/DB). Please use this script strictly for personal educational purposes. All data copyrights belong to Oxford University Press and the original data providers.
