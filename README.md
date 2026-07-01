# OALD10-Yomitan-Converter (Dictionary Builder)

An advanced Python script to deeply parse, clean, and restructure the **Oxford Advanced Learner's Dictionary (10th Ed) EN-ZH** MDX data into a highly optimized, native Yomitan/Yomichan JSON dictionary.

## 🌟 Features (V2.0 核心特性)

Unlike raw MDX conversions (e.g., via PyGlossary) which result in cluttered HTML layouts and broken labels, this script features a completely decoupled **Extractor-Renderer architecture** designed specifically for this dictionary to guarantee the best reading experience on Yomitan flashcards:

- **Advanced Tag System (标签重构与色彩分层)**: Fully maps 28 grammatical parts of speech, CEFR difficulty levels (A1-C2), and Oxford 3000/5000/OPAL core vocabularies. Applies a strict visual hierarchy (Gray -> Blue -> Green -> Purple) to eliminate tag clutter.
- **Deep Panel Restructuring (18大面板精细解构)**: Surgically extracts 18 complex HTML panels (e.g., *Word Origin*, *Collocations*, *Which Word*). Long, disruptive panels are elegantly relegated to the bottom of the entry, keeping the primary definitions strictly at the top.
- **Smart Example Filtering (智能例句优选与防信息过载)**: Accurately sniffs `[AI Translation]` and `[Proofread]` tags. Automatically sorts examples by quality and rigorously truncates to a maximum of 5 examples per main sense to prevent Anki card overload.
- **Hash Deduplication & De-inflection (哈希去重与时态逆推)**: Eliminates duplicate entries caused by UK/US spelling variants via JSON hash checks. Completely restores POS rule mappings so searching for inflected forms (e.g., `reading`) perfectly matches the root (`read`).
- **Anki Copy-Paste Friendly (防粘连格式)**: Invisible physical spaces are injected into the DOM tree. Copying text directly from the Yomitan popup will no longer result in tags and definitions sticking together.
- **Internationalization (i18n 国际化)**: Native support for both Bilingual (EN-ZH) and Monolingual (EN-EN) outputs, with customizable UI languages for Yomitan tags.

---

## 📸 Screenshots (实际效果)

*(A clean layout, native Yomitan tag coloring, smart example sorting, and deep panel extraction.)*

**Clean Layout & Deep Restructuring (纯净排版与特种面板解析)**

<img alt="image" src="https://github.com/user-attachments/assets/97b13623-ba10-4feb-8ea1-ea3403d8552c" />


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

**Arguments Documentation**:
- `-i` or `--input`: (Required) Path to the extracted MDX text file.
- `-o` or `--output`: (Optional) Path to save the Yomitan JSON files. Defaults to `./yomitan_v2`.
- `-m` or `--mode`: Dictionary content mode. `bilingual` (default) or `mono` (English-only definitions).
- `-u` or `--ui-lang`: Language for UI tags and descriptions. `zh` (default) or `en`.

3. Wait for the magic to happen! The script will parse the data, generate the dictionaries, write data forensic reports, and automatically pack everything into a final zip file (e.g., `OALD10_Yomitan_V2.0.0.zip` or `OALD10_Yomitan_V2.0.0_Immersion.zip`).

4. **Import to Yomitan**: Open your Yomitan settings, go to Dictionaries, and import the newly generated `.zip` file directly. Done!

---

## ⚖️ License (开源协议)
This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0).
You are free to use, modify, and distribute this software, but any derivative works (including modifications or providing it as a network service) must strictly be open-sourced under the same license.

---

## ⚠️ Disclaimer (免责声明)
This repository ONLY contains the Python processing script. It does NOT contain, distribute, or host any copyrighted dictionary data (HTML/MDX/DB). Please use this script strictly for personal educational purposes. All data copyrights belong to Oxford University Press and the original data providers.
