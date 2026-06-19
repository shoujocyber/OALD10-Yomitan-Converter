# OALD 10 to Yomitan Dictionary Builder

An advanced Python script to deeply parse, clean, and restructure the **Oxford Advanced Learner's Dictionary (10th Ed) EN-ZH** MDX data into a highly optimized, native Yomitan/Yomichan JSON dictionary.

## 🌟 Features (核心特性)

Unlike raw MDX conversions (e.g., via PyGlossary) which result in cluttered HTML layouts and overlapping labels, this script performs a "surgical extraction" specifically tailored for this dictionary to guarantee the best reading experience on Yomitan flashcards:

- **Ultimate Aggregation Engine (终极聚合引擎)**: Automatically resolves multi-directional redirects and folds identical upstream definitions (like UK/US spelling variants) into a single, clean entry using Joint Primary Key deduplication.
- **Intelligent Example Sorting (智能例句优选)**: Prioritizes official translations. Relegates machine translation `[AI机翻]` and unofficial proofreading `[个人审校]` to the bottom, or drops them entirely if official examples are sufficient.
- **Construction Frames (语法句型框)**: Extracts syntactic patterns (e.g., `[read something into something]`) and elegantly prefixes them to examples and definitions.
- **Tag Isolation & Native Badges (标签防污染与原生高亮)**: Strict DOM tree isolation prevents global tags from polluting child idioms. Auto-generates `tag_bank_1.json` for beautiful, native Yomitan part-of-speech badges.
- **1-Click Auto-Packaging (一键全自动打包)**: Automatically generates `index.json`, compresses all chunks into a final `.zip` file, and cleans up temporary JSON fragments.

---

## 📸 Screenshots (实际效果)

*(Here you can see the clean layout, native Yomitan tag coloring, and smart example sorting.)*

**1. Clean Layout & Native Tags (纯净排版与原生标签)**
<img width="1006" height="1156" alt="Image" src="https://github.com/user-attachments/assets/09355a1b-07af-473c-9235-573bf8b1d610" />

**2. Idioms & Phrasal Verbs (习语与短语动词聚合)**
<img width="989" height="1142" alt="Image" src="https://github.com/user-attachments/assets/1c659f04-ffed-43b3-b864-015e6438b1bc" />

---

## 📋 Prerequisites (环境要求)

- **Python**: Version 3.10 or higher.
- **OS**: Windows, macOS, or Linux.

---

## 🛠️ How to Build (如何自己构建)

Because of copyright restrictions, **this repository DOES NOT contain the dictionary data**. You must build it yourself using the original MDX file.

### Step 1: Obtain the MDX (获取原始词典)
This script is strictly designed to parse the **OALD 10th Edition** shared by xingxingla on the Freemdict Forum.
🔗 **Source link**: [精装 - 牛津高阶双解第10版完美版重生版（OALDPEX） - Freemdict Forum](https://forum.freemdict.com/t/topic/43710)
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
1. Install the HTML parsing library:
```bash
pip install beautifulsoup4
```
2. Run the conversion script using the command line:
```bash
python main.py -i path/to/your/oaldpe.txt -o path/to/output_folder
```
- -i or --input: (Required) Path to the extracted MDX text file.
- -o or --output: (Optional) Path to save the Yomitan JSON files. Defaults to ./yomitan_out.

3. Wait for the magic to happen! The script will parse the data, generate the dictionaries, write data forensic reports, and automatically pack everything into a final zip file (e.g., OALD10_Yomitan_v1.2.0.zip).

4. Import to Yomitan: Open your Yomitan settings, go to Dictionaries, and import the newly generated .zip file directly. Done!

---

## ⚠️ Disclaimer
This repository ONLY contains the Python processing script. It does NOT contain, distribute, or host any copyrighted dictionary data (HTML/MDX/DB). Please use this script strictly for personal educational purposes. All data copyrights belong to Oxford University Press and the original data providers.