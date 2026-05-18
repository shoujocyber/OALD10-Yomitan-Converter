# OALD 10 to Yomitan Dictionary Builder

An advanced Python script to deeply parse, clean, and restructure the **Oxford Advanced Learner's Dictionary (10th Ed) EN-ZH** MDX data into a highly optimized, native Yomitan/Yomichan JSON dictionary.

## 🌟 Features (核心特性)

Unlike raw MDX conversions (e.g., via PyGlossary) which result in cluttered HTML layouts and overlapping labels, this script performs a "surgical extraction" specifically tailored for this dictionary to guarantee the best reading experience on Yomitan flashcards:

- **Intelligent Example Sorting (智能例句优选)**: Prioritizes official translations. Relegates machine translation `[AI机翻]` and unofficial proofreading `[个人审校]` to the bottom, or drops them entirely if official examples are sufficient.
- **Construction Frames (语法句型框)**: Extracts syntactic patterns (e.g., `[read something into something]`) and elegantly prefixes them to examples and definitions.
- **Tag Deduplication (防标签吞噬)**: Merges and deduplicates global and local meta-tags (e.g., `[informal]`, `[singular]`) to prevent layout bugs.
- **Cross-References & Idioms (词汇网络)**: Gracefully appends synonyms (`🔗 synonym`), related words, idioms (`📌`), and lists related Phrasal Verbs at the bottom of the entry.

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

### Step 4: Run the Parser (运行清洗脚本)
1. Install the HTML parsing library:
```bash
pip install beautifulsoup4
```
2. Run the script:
```bash
python main.py
```
Wait for the script to finish. It will parse ~62,000 core words and expand them to ~700,000 terms (including inflections), outputting them into a new folder named `yomitan_out/`.

### Step 5: Package for Yomitan (打包为Yomitan格式)
1. Create a file named `index.json` in the `yomitan_out/` folder and paste this metadata:
```json
{
  "title": "Oxford Advanced Learner's Dictionary",
  "format": 3,
  "revision": "v1.0.0",
  "sequenced": true,
  "author": "Open Source Converter",
  "url": "https://github.com/shoujocyber/OALD10-Yomitan-Converter",
  "description": "牛津高阶英汉双解词典(第10版)纯净版"
}
```
2. Create a file named `tag_bank_1.json` in the `yomitan_out/` folder to enable native coloring in Yomitan:
```json
[
  ["noun", "partOfSpeech", 0, "名词 (Noun)", 0],
  ["verb", "partOfSpeech", 0, "动词 (Verb)", 0],
  ["adjective", "partOfSpeech", 0, "形容词 (Adjective)", 0],
  ["adverb", "partOfSpeech", 0, "副词 (Adverb)", 0],
  ["pronoun", "partOfSpeech", 0, "代词 (Pronoun)", 0],
  ["preposition", "partOfSpeech", 0, "介词 (Preposition)", 0],
  ["conjunction", "partOfSpeech", 0, "连词 (Conjunction)", 0],
  ["interjection", "partOfSpeech", 0, "感叹词 (Interjection)", 0],
  ["determiner", "partOfSpeech", 0, "限定词 (Determiner)", 0],
  ["idiom", "expression", 0, "习语 (Idiom)", 0],
  ["phrasal verb", "expression", 0, "动词短语 (Phrasal Verb)", 0],
  ["Oxford Advanced Learner's Dictionary", "dictionary", -10, "牛津高阶英汉双解词典 第10版", 0]
]
```
3. **Zip it!** Select all `.json` files inside the `yomitan_out/` folder and compress them into a `.zip` archive (do not zip the folder itself, zip the files). 
4. Import the `.zip` file into Yomitan.

---

## ⚠️ Disclaimer
This repository ONLY contains the Python processing script. It does NOT contain, distribute, or host any copyrighted dictionary data (HTML/MDX/DB). Please use this script strictly for personal educational purposes. All data copyrights belong to Oxford University Press and the original data providers.
