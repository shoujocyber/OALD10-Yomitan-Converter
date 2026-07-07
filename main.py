#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ==============================================================================
# OALD10-Yomitan-Converter
# Copyright (C) 2026 shoujocyber
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# ==============================================================================

import json
import os
import re
import zipfile
import glob
import time
from bs4 import BeautifulSoup
from tqdm import tqdm

VERSION = "3.0.0"
AUTHOR = "shoujocyber"

# ==========================================
# 🌍 i18n Dictionary for UI & Metadata
# ==========================================
I18N_TEXT = {
    "zh": {
        "desc_bilingual": "牛津高阶英汉双解词典(第10版) 纯净优化版",
        "desc_mono": "牛津高阶词典(第10版) 沉浸英英版",
        "ai_trans": "[AI机翻] ",
        "proofread": "[个人审校] ",
        "tags": {
            "noun": "名词 (Noun)", "verb": "动词 (Verb)", "adj": "形容词 (Adjective)",
            "adv": "副词 (Adverb)", "pron": "代词 (Pronoun)", "prep": "介词 (Preposition)",
            "conj": "连词 (Conjunction)", "excl": "感叹词 (Exclamation)", "det": "限定词 (Determiner)",
            "def-article": "定冠词 (Definite Article)", "indef-article": "不定冠词 (Indefinite Article)",
            "num": "数词 (Number)", "ordinal-num": "序数词 (Ordinal Number)",
            "modal": "情态动词 (Modal Verb)", "aux": "助动词 (Auxiliary Verb)",
            "linking-v": "连系动词 (Linking Verb)", "phrasal-v": "动词短语 (Phrasal Verb)",
            "prefix": "前缀 (Prefix)", "suffix": "后缀 (Suffix)", "combining-form": "组合形式 (Combining Form)",
            "inf-marker": "不定式标记 (Infinitive Marker)", "short-form": "缩略形式 (Short Form)",
            "abbr": "缩写 (Abbreviation)", "noun/adj": "名词/形容词", "idiom": "习语 (Idiom)",
            "symb": "符号 (Symbol)",
            "A1": "CEFR 难度: A1", "A2": "CEFR 难度: A2", "B1": "CEFR 难度: B1",
            "B2": "CEFR 难度: B2", "C1": "CEFR 难度: C1", "C2": "CEFR 难度: C2",
            "Oxford3000": "牛津 3000 核心词汇", "Oxford5000": "牛津 5000 核心词汇",
            "OPAL": "牛津学术词汇 (OPAL)", "redirect": "重定向"
        }
    },
    "en": {
        "desc_bilingual": "Oxford Advanced Learner's Dictionary 10th (Bilingual Edition)",
        "desc_mono": "Oxford Advanced Learner's Dictionary 10th (Monolingual Edition)",
        "ai_trans": "[AI Translation] ",
        "proofread": "[Proofread] ",
        "tags": {
            "noun": "Noun", "verb": "Verb", "adj": "Adjective",
            "adv": "Adverb", "pron": "Pronoun", "prep": "Preposition",
            "conj": "Conjunction", "excl": "Exclamation", "det": "Determiner",
            "def-article": "Definite Article", "indef-article": "Indefinite Article",
            "num": "Number", "ordinal-num": "Ordinal Number",
            "modal": "Modal Verb", "aux": "Auxiliary Verb",
            "linking-v": "Linking Verb", "phrasal-v": "Phrasal Verb",
            "prefix": "Prefix", "suffix": "Suffix", "combining-form": "Combining Form",
            "inf-marker": "Infinitive Marker", "short-form": "Short Form",
            "abbr": "Abbreviation", "noun/adj": "Noun/Adjective", "idiom": "Idiom",
            "symb": "Symbol",
            "A1": "CEFR Level: A1", "A2": "CEFR Level: A2", "B1": "CEFR Level: B1",
            "B2": "CEFR Level: B2", "C1": "CEFR Level: C1", "C2": "CEFR Level: C2",
            "Oxford3000": "Oxford 3000 Core Vocabulary", "Oxford5000": "Oxford 5000 Core Vocabulary",
            "OPAL": "Oxford Phrasal Academic Lexicon (OPAL)", "redirect": "Redirect"
        }
    }
}

# ==========================================
# Core Configuration
# ==========================================
DEFAULT_TEST_WORDS = ("read", "excited", "as", "afaic", "turn-around", "an", "a", "cry", "take", "get", "anyhow", "judgement")

LABEL_DECORATION_RE = re.compile('^[\\s:\uff1a]+|[\\s:\uff1a]+$')
UNSAFE_STRUCTURED_KEYS = {"style"}


def normalize_label(label):
    text = re.sub(r'\s+', ' ', str(label or '')).strip()
    return LABEL_DECORATION_RE.sub('', text).strip()


XREF_LABELS = {
    "zh": {
        "see also": "See also 参见",
        "synonym": "Synonym 同义词",
        "compare": "Compare 对比参见",
        "opposite": "Opposite 反义词",
        "root": "Root 词根",
        "derivative": "Derivative 派生词",
        "phrasal verbs": "Phrasal verbs 短语动词",
        "related noun": "Related noun 相关名词",
        "past tense, past participle of": "Past tense, past participle of 过去式/过去分词",
        "past tense of": "Past tense of 过去式",
        "past participle of": "Past participle of 过去分词",
        "present participle of": "Present participle of 现在分词",
        "plural of": "Plural of 复数形式",
        "third person of": "Third person of 第三人称单数形式",
        "note at": "Note at 用法说明见",
        "=": "Equivalent 等同",
        "at": "At 见",
        "language bankat": "Language bank 语言库",
        "synonymsat": "Synonyms 辨析",
        "homophonesat": "Homophones 同音词",
        "wordfinder noteat": "Wordfinder 词汇扩展",
        "collocationsat": "Collocations 搭配",
    },
    "en": {
        "see also": "See also",
        "synonym": "Synonym",
        "compare": "Compare",
        "opposite": "Opposite",
        "root": "Root",
        "derivative": "Derivative",
        "phrasal verbs": "Phrasal verbs",
        "related noun": "Related noun",
        "past tense, past participle of": "Past tense, past participle of",
        "past tense of": "Past tense of",
        "past participle of": "Past participle of",
        "present participle of": "Present participle of",
        "plural of": "Plural of",
        "third person of": "Third person of",
        "note at": "Note at",
        "=": "Equivalent",
        "at": "At",
        "language bankat": "Language bank",
        "synonymsat": "Synonyms",
        "homophonesat": "Homophones",
        "wordfinder noteat": "Wordfinder",
        "collocationsat": "Collocations",
    },
}


def format_xref_label(label, ui_lang):
    clean_label = normalize_label(label)
    label_key = clean_label.lower()
    return XREF_LABELS.get(ui_lang, {}).get(label_key, clean_label)


def sanitize_structured_content(value, allow_open=False):
    if isinstance(value, list):
        return [sanitize_structured_content(item, allow_open=allow_open) for item in value]
    if isinstance(value, dict):
        blocked = UNSAFE_STRUCTURED_KEYS if allow_open else UNSAFE_STRUCTURED_KEYS | {"open"}
        return {
            key: sanitize_structured_content(item, allow_open=allow_open)
            for key, item in value.items()
            if key not in blocked
        }
    return value


def remove_generated_file(path, warn=False):
    last_error = None
    for attempt in range(5):
        try:
            os.remove(path)
            return True
        except FileNotFoundError:
            return True
        except OSError as exc:
            last_error = exc
            if attempt < 4:
                time.sleep(0.05)
    if warn:
        print(f"[WARN] Could not remove generated file: {path} ({last_error})")
    return False


def get_zip_filename(mode, ui_lang, debug_mode=False):
    zip_filename = f"OALD10_Yomitan_Test" if debug_mode else f"OALD10_Yomitan_V{VERSION}"
    if mode == "mono" and ui_lang == "en":
        zip_filename += "_Global.zip"
    elif mode == "mono":
        zip_filename += "_Immersion.zip"
    elif ui_lang == "en":
        zip_filename += "_EN_Tags.zip"
    else:
        zip_filename += ".zip"
    return zip_filename


def cleanup_output_dir(output_dir, zip_filename=None):
    generated_patterns = [
        "term_bank_*.json",
        "index.json",
        "tag_bank_1.json",
        "styles.css",
    ]
    for pattern in generated_patterns:
        for path in glob.glob(os.path.join(output_dir, pattern)):
            remove_generated_file(path)
    if zip_filename:
        remove_generated_file(os.path.join(output_dir, zip_filename))

# ==========================================
# 🎨 Dynamic CSS Generation Engine
# ==========================================
def generate_css(mode):
    ex_indent = "0.95em" if mode == "mono" else "1.35em"
    def_font_size = "1.07em" if mode == "mono" else "1.04em"
    def_font_weight = "550" if mode == "mono" else "500"
    def_margin_bottom = "6px" if mode == "mono" else "2px"
    ex_font_size = "0.99em" if mode == "mono" else "1em"
    ex_opacity = "0.96" if mode == "mono" else "1"
    return f"""/* OALD 10 Yomitan Stylesheet */
[data-sc-class="oald-bold"] {{ font-weight: 700; }}
[data-sc-class="oald-gloss"] {{ color: #888; }}

/* 👑 核心布局：精准负边距悬挂 */
div[data-sc-class="oald-sense"] {{ padding-left: 1.72em; margin-bottom: 10px; line-height: 1.52; }}
div[data-sc-class="oald-sense-single"] {{ margin-bottom: 10px; line-height: 1.52; }}

div[data-sc-class="oald-sense-header"], div[data-sc-class="oald-sense-header-numbered"] {{ margin-bottom: 3px; }}
div[data-sc-class="oald-sense-header"] {{ display: block; }}
div[data-sc-class="oald-sense-header-numbered"] {{ margin-left: -1.72em; padding-left: 1.72em; position: relative; display: block; min-width: 0; }}

span[data-sc-class="oald-def-num"] {{ position: absolute; left: 0; width: 1.25em; display: inline-block; text-align: center; font-weight: 800; font-size: 1.05em; color: var(--text-color); }}
span[data-sc-class="oald-head-main"] {{ display: inline; min-width: 0; }}
span[data-sc-class="oald-shortcut"] {{ display: inline-block; vertical-align: baseline; max-width: 100%; box-sizing: border-box; font-size: 0.84em; font-weight: 600; line-height: 1.36; color: var(--text-color); color: color-mix(in srgb, var(--text-color) 76%, #B56A2A 24%); background-color: rgba(181, 106, 42, 0.12); border: 1px solid rgba(181, 106, 42, 0.26); border-left: 2px solid rgba(181, 106, 42, 0.62); border-radius: 4px; padding: 0 5px; margin-right: 0.35em; white-space: normal; overflow-wrap: break-word; }}
span[data-sc-class="oald-idiom-title"] {{ font-weight: 700; color: #B63F5A; margin-right: 0.45em; }}

/* 现代微缩标签 (Pill Tags) - 去除斜体，双色分类，加大字号 */
span[data-sc-class="oald-tag-grammar"] {{ display: inline-block; vertical-align: baseline; box-sizing: border-box; background-color: rgba(0, 120, 215, 0.08); color: var(--text-color); color: color-mix(in srgb, var(--text-color) 72%, #0078D7 28%); border: 1px solid rgba(0, 120, 215, 0.30); border-left: 2px solid rgba(0, 120, 215, 0.62); border-radius: 4px; padding: 0 5px; font-size: 0.84em; line-height: 1.36; font-weight: 550; font-family: sans-serif; white-space: nowrap; margin-right: 0.35em; }}
span[data-sc-class="oald-tag-grammar-long"] {{ display: inline-block; vertical-align: baseline; max-width: 100%; box-sizing: border-box; background-color: rgba(0, 120, 215, 0.08); color: var(--text-color); color: color-mix(in srgb, var(--text-color) 72%, #0078D7 28%); border: 1px solid rgba(0, 120, 215, 0.30); border-left: 2px solid rgba(0, 120, 215, 0.62); border-radius: 4px; padding: 0 5px; font-size: 0.84em; line-height: 1.36; font-weight: 550; font-family: sans-serif; white-space: normal; overflow-wrap: break-word; margin-right: 0.35em; }}
span[data-sc-class="oald-tag-other"] {{ background-color: rgba(128, 128, 128, 0.08); color: var(--text-color); border: 1px solid rgba(128, 128, 128, 0.28); border-radius: 4px; padding: 0 5px; font-size: 0.88em; font-family: sans-serif; white-space: nowrap; opacity: 0.82; margin-right: 0.35em; display: inline-block; vertical-align: baseline; }}
span[data-sc-class="oald-tag-topic"] {{ display: inline-block; vertical-align: baseline; max-width: 100%; box-sizing: border-box; background-color: rgba(112, 122, 36, 0.10); color: var(--text-color); color: color-mix(in srgb, var(--text-color) 70%, #707A24 30%); border: 1px solid rgba(112, 122, 36, 0.32); border-left: 2px solid rgba(112, 122, 36, 0.66); border-radius: 4px; padding: 0 5px; font-size: 0.84em; line-height: 1.36; font-weight: 600; font-family: sans-serif; white-space: normal; overflow-wrap: break-word; margin-right: 0.35em; }}
span[data-sc-class="oald-variant-inline"] {{ display: inline-block; vertical-align: baseline; max-width: 100%; box-sizing: border-box; font-size: 0.91em; font-style: normal; font-weight: 500; line-height: 1.36; color: var(--text-color); color: color-mix(in srgb, var(--text-color) 82%, #777 18%); opacity: 0.90; background-color: rgba(128, 128, 128, 0.10); border: 1px solid rgba(128, 128, 128, 0.22); border-radius: 3px; padding: 0 0.32em; margin-right: 0.45em; white-space: normal; overflow-wrap: break-word; }}

/* 大句型 [+ speech] - 绝对禁止断行 */
span[data-sc-class="oald-pattern"] {{ font-weight: 700; color: #007F7A; white-space: nowrap; font-size: 0.94em; margin-right: 0.35em; display: inline-block; }}

/* 👑 正文与例句 (含例句开头的句型高亮) */
div[data-sc-class="oald-eng"] {{ margin-top: 2px; margin-bottom: {def_margin_bottom}; line-height: 1.5; font-size: {def_font_size}; font-weight: {def_font_weight}; color: var(--text-color); opacity: 0.98; }}
div[data-sc-class="oald-chn"] {{ font-size: 1.01em; font-weight: 700; margin-bottom: 5px; line-height: 1.46; color: var(--text-color); }}
div[data-sc-class="oald-ex-en"], div[data-sc-class="oald-panel-ex-en"] {{ padding-left: {ex_indent}; text-indent: -{ex_indent}; margin-bottom: 1px; line-height: 1.42; font-size: {ex_font_size}; color: var(--text-color); opacity: {ex_opacity}; }}
div[data-sc-class="oald-ex-zh"], div[data-sc-class="oald-panel-ex-zh"] {{ padding-left: {ex_indent}; text-indent: -{ex_indent}; margin-bottom: 4px; line-height: 1.42; }}
span[data-sc-class="oald-sym"] {{ opacity: 0.58; font-family: Arial, sans-serif; display: inline-block; width: {ex_indent}; text-indent: 0; }}
span[data-sc-class="oald-ex-pattern"] {{ color: #007F7A; font-weight: 700; margin-right: 0; }}

/* Cross-reference links, such as See also and Phrasal verbs. */
/* 废除 Flex 布局，防止短语列表断裂。加入链接防断行护盾 */
div[data-sc-class="oald-link"] {{ margin-top: 2px; margin-bottom: 4px; font-size: 0.95em; display: block; line-height: 1.6; word-break: break-word; }}
div[data-sc-class="oald-link"] a {{ white-space: nowrap; }}
span[data-sc-class="oald-cross-ref-icon"] {{ font-weight: 700; color: #0078D7 !important; font-size: 1.05em; font-family: Arial, sans-serif; }}
span[data-sc-class="oald-label"] {{ font-weight: 700; color: var(--text-color); opacity: 0.84; font-style: normal; }}

/* 面板区压缩 */
details[data-sc-class="oald-panel"] {{ margin: 2px 0; padding: 0; }}
summary[data-sc-class="oald-panel-title"] {{ font-weight: 700; cursor: pointer; color: var(--text-color); line-height: 1.32; padding: 1px 0; margin: 0; }}
div[data-sc-class="oald-panel-content"] {{ background-color: rgba(128, 128, 128, 0.05); border-left: 3px solid #4285f4; border-radius: 0 4px 4px 0; padding: 6px 8px; margin-top: 4px; }}
div[data-sc-class="oald-group"] {{ font-weight: 700; color: #0078D7; margin-top: 4px; margin-bottom: 2px; font-size: 0.95em; }}
div[data-sc-class="oald-panel-indent"] {{ padding-left: 1.2em; margin-top: 2px; margin-bottom: 2px; }}

/* 词条头部附属 */
div[data-sc-class="oald-entry-head"] {{ border-bottom: 2px solid #4285f4; padding-bottom: 4px; margin-bottom: 8px; margin-top: 4px; }}
span[data-sc-class="oald-headword"] {{ font-size: 1.6em; font-weight: 700; margin-right: 8px; }}
span[data-sc-class="oald-pos"] {{ font-size: 1.1em; color: #0078D7; font-family: serif; }}
div[data-sc-class="oald-phonetics"] {{ margin-bottom: 4px; opacity: 0.9; margin-top: 4px; }}
div[data-sc-class="oald-variant"] {{ opacity: 0.8; font-style: italic; margin-bottom: 4px; }}
div[data-sc-class="oald-derivative"] {{ margin-top: 8px; border-top: 1px dashed rgba(128,128,128,0.5); padding-top: 4px; padding-left: 0.5em; }}
span[data-sc-class="oald-derivative-word"] {{ font-weight: 700; color: #0078D7; }}
"""

# ==========================================
# Module 1: Data Extractor
# ==========================================
class OaldExtractor:
    def __init__(self, mode="bilingual", ui_lang="zh"):
        self.mode = mode
        self.ui_lang = ui_lang
        self.i18n = I18N_TEXT[ui_lang]
        self.stats = {"vip_parsed": {}, "fallback": {}, "errors": {}}

    def clean_text(self, text):
        if not text: return ""
        text = re.sub(r'\s+', ' ', text).strip()
        return text.replace("( ", "(").replace(" )", ")")

    def _mark_rich_text(self, node):
        if not node: return
        for eb in node.find_all(['span', 'a', 'strong', 'b'], class_=['eb', 'ei', 'Ref', 'cl', 'xh_bold', 'xh', 'ndv']):
            eb.replace_with(f"⚑{eb.get_text(strip=True)}⚐")
        for gloss in node.find_all('span', class_='gloss'):
            gloss.replace_with(f"★{gloss.get_text(strip=True)}☆")

    def _parse_panel(self, unbox):
        utype = unbox.get('unbox')
        title_en = utype.capitalize()
        title_zh = ""
        title_node = unbox.find('span', class_='box_title')
        if title_node:
            zh_node = title_node.find('unboxx')
            if zh_node:
                title_zh = zh_node.get_text(strip=True) if self.ui_lang == "zh" else ""
                zh_node.decompose()
            title_en = self.clean_text(title_node.get_text())
            title_node.decompose()

        panel_data = {"type": utype, "title_en": title_en, "title_zh": title_zh, "data": []}
        body = unbox.find('span', class_='body')
        c_root = body if body else unbox

        try:
            if utype == 'cult':
                for p in c_root.find_all('span', class_='p'):
                    zh_node = p.find(lambda t: t.name in ['ubx', 'chn', 'undt'])
                    zh_text = zh_node.get_text(strip=True) if zh_node else ""
                    if zh_node: zh_node.decompose()
                    self._mark_rich_text(p)
                    panel_data["data"].append({"en": self.clean_text(p.get_text()), "zh": zh_text})

            elif utype == 'wordorigin':
                p = c_root.find('span', class_='p')
                if p:
                    zh_node = p.find(lambda t: t.name in ['ubx', 'chn', 'undt'])
                    zh_txt = zh_node.get_text(strip=True) if zh_node else ""
                    if zh_node: zh_node.decompose()
                    self._mark_rich_text(p)
                    panel_data["data"] = {"en": self.clean_text(p.get_text()), "zh": zh_txt}
                else:
                    panel_data["data"] = {"en": self.clean_text(c_root.get_text()), "zh": ""}

            elif utype == 'colloc':
                sections = []
                current_sec = {"group_en": "", "group_zh": "", "items": []}
                for child in c_root.children:
                    if child.name == 'span' and 'unbox' in child.get('class', []):
                        if current_sec["items"] or current_sec["group_en"]:
                            sections.append(current_sec)
                            current_sec = {"group_en": "", "group_zh": "", "items": []}
                        zh_node = child.find(['undt', 'chn'])
                        current_sec["group_zh"] = zh_node.get_text(strip=True) if zh_node else ""
                        if zh_node: zh_node.decompose()
                        current_sec["group_en"] = self.clean_text(child.get_text())
                    elif child.name == 'ul' and 'bullet' in child.get('class', []):
                        for li in child.find_all('li', class_='li'):
                            zh_node = li.find(['undt', 'chn'])
                            zh_txt = zh_node.get_text(strip=True) if zh_node else ""
                            if zh_node: zh_node.decompose()
                            self._mark_rich_text(li)
                            current_sec["items"].append({"en": self.clean_text(li.get_text()), "zh": zh_txt})
                if current_sec["items"] or current_sec["group_en"]: sections.append(current_sec)
                panel_data["data"] = sections

            elif utype in ['langbank', 'which_word', 'british_american', 'wordfinder', 'wordfamily', 'grammar', 'more_about', 'express', 'vocab']:
                sections = []
                current_sec = {"subtitle_en": "", "subtitle_zh": "", "items": []}
                for child in c_root.children:
                    if child.name == 'span' and 'unbox' in child.get('class', []):
                        if child.find_parent('li'): continue
                        if current_sec["items"] or current_sec["subtitle_en"]:
                            sections.append(current_sec)
                            current_sec = {"subtitle_en": "", "subtitle_zh": "", "items": []}
                        zh_node = child.find(['undt', 'chn'])
                        current_sec["subtitle_zh"] = zh_node.get_text(strip=True) if zh_node else ""
                        if zh_node: zh_node.decompose()
                        current_sec["subtitle_en"] = self.clean_text(child.get_text())
                    elif child.name == 'ul' and 'bullet' in child.get('class', []):
                        for li in child.find_all('li', class_='li', recursive=False):
                            li_chunks = []
                            cur_en, cur_zh = [], []
                            for el in li.children:
                                if el.name == 'ul' and 'examples' in el.get('class', []):
                                    en_str = self.clean_text(" ".join(cur_en))
                                    zh_str = self.clean_text(" ".join(cur_zh))
                                    ex_list = []
                                    for ex_li in el.find_all('li'):
                                        unx = ex_li.find('span', class_='unx')
                                        if unx: self._mark_rich_text(unx)
                                        ex_en = self.clean_text(unx.get_text()) if unx else ""
                                        if unx: unx.decompose()
                                        ex_zh_node = ex_li.find(lambda t: t.name in ['unxt', 'undt', 'chn'])
                                        ex_zh = ex_zh_node.get_text(strip=True) if ex_zh_node else ""
                                        ex_list.append({"en": ex_en, "zh": ex_zh})
                                    li_chunks.append({"en": en_str, "zh": zh_str, "examples": ex_list})
                                    cur_en, cur_zh = [], []
                                elif el.name in ['undt', 'chn'] or (el.name == 'span' and 'undt' in el.get('class', [])):
                                    cur_zh.append(el.get_text(strip=True))
                                else:
                                    if el.name:
                                        self._mark_rich_text(el)
                                        cur_en.append(el.get_text(separator=' ', strip=True))
                                    else:
                                        if str(el).strip(): cur_en.append(str(el).strip())

                            en_str = self.clean_text(" ".join(cur_en))
                            zh_str = self.clean_text(" ".join(cur_zh))
                            if en_str or zh_str:
                                li_chunks.append({"en": en_str, "zh": zh_str, "examples": []})
                            current_sec["items"].extend(li_chunks)
                if current_sec["items"] or current_sec["subtitle_en"]: sections.append(current_sec)
                panel_data["data"] = sections

            elif utype == 'synonyms':
                intro_en, intro_zh = "", ""
                p_node = c_root.find('span', class_='p')
                if p_node:
                    zh_node = p_node.find(['undt', 'chn'])
                    intro_zh = zh_node.get_text(strip=True) if zh_node else ""
                    if zh_node: zh_node.decompose()
                    self._mark_rich_text(p_node)
                    intro_en = self.clean_text(p_node.get_text())
                    p_node.decompose()

                syn_list = []
                deflist = c_root.find('span', class_='deflist')
                if deflist:
                    for defpara in deflist.find_all('span', class_='defpara'):
                        eb = defpara.find('span', class_='eb')
                        eb_txt = eb.get_text(strip=True) if eb else ""
                        if eb: eb.decompose()
                        zh_node = defpara.find(['undt', 'chn'])
                        zh_txt = zh_node.get_text(strip=True) if zh_node else ""
                        if zh_node: zh_node.decompose()
                        ex_data = []
                        ex_ul = defpara.find('ul', class_='examples')
                        if ex_ul:
                            for unx in ex_ul.find_all('span', class_='unx'):
                                ex_chn_node = unx.find(['unxt', 'chn'])
                                ex_chn = ex_chn_node.get_text(strip=True) if ex_chn_node else ""
                                if ex_chn_node: ex_chn_node.decompose()
                                self._mark_rich_text(unx)
                                ex_data.append({"en": self.clean_text(unx.get_text()), "zh": ex_chn})
                            ex_ul.decompose()
                        self._mark_rich_text(defpara)
                        syn_list.append({"highlight": eb_txt, "en": self.clean_text(defpara.get_text()), "zh": zh_txt, "examples": ex_data})
                panel_data["data"] = {"intro_en": intro_en, "intro_zh": intro_zh, "items": syn_list}

            elif utype == 'verbforms':
                for tr in c_root.find_all('tr', class_='verb_form'):
                    form_name = tr.find('span', class_='vf_prefix')
                    form_name_txt = form_name.get_text(strip=True) if form_name else ""
                    td_form = tr.find('td', class_='verb_form')
                    form_val = td_form.get_text(strip=True).replace(form_name_txt, '').strip() if td_form else ""
                    phon = {}
                    uk_phon = tr.find('div', class_='phons_br')
                    us_phon = tr.find('div', class_='phons_n_am')
                    if uk_phon and uk_phon.find('span', class_='phon'): phon["uk"] = uk_phon.find('span', class_='phon').get_text(strip=True)
                    if us_phon and us_phon.find('span', class_='phon'): phon["us"] = us_phon.find('span', class_='phon').get_text(strip=True)
                    panel_data["data"].append({"form": form_name_txt, "word": form_val, "phonetics": phon})

            elif utype == 'homophone':
                for li in c_root.find_all('li', class_='li'):
                    eb = li.find('span', class_='eb')
                    eb_txt = eb.get_text(strip=True) if eb else ""
                    if eb: eb.decompose()
                    ex_node = li.find('ul', class_='examples')
                    ex_en, ex_zh = "", ""
                    if ex_node:
                        unx = ex_node.find('span', class_='unx')
                        if unx:
                            zh_node = unx.find(['unxt', 'chn'])
                            ex_zh = zh_node.get_text(strip=True) if zh_node else ""
                            if zh_node: zh_node.decompose()
                            self._mark_rich_text(unx)
                            ex_en = self.clean_text(unx.get_text())
                        ex_node.decompose()
                    pos_txt = self.clean_text(li.get_text())
                    panel_data["data"].append({"word": eb_txt, "pos_info": pos_txt, "example_en": ex_en, "example_zh": ex_zh})

            elif utype == 'snippet':
                 if c_root.find('ul', class_='collocs_list'):
                     sections = []
                     for child in c_root.children:
                         if child.name == 'span' and 'unbox' in child.get('class', []):
                             sections.append({"title": self.clean_text(child.get_text()), "items": []})
                         elif child.name == 'ul' and 'collocs_list' in child.get('class', []):
                             items = [self.clean_text(li.get_text()) for li in child.find_all('li')]
                             if sections: sections[-1]["items"].extend(items)
                     panel_data["data"] = sections
                 else:
                     panel_data["data"] = self.clean_text(c_root.get_text())

            elif utype == 'extra_examples':
                for ex in c_root.find_all('span', class_=['unx', 'x']):
                    zh_node = ex.find(['unxt', 'chn'])
                    prefix_tag = ""
                    if zh_node:
                        if zh_node.find('ai'): prefix_tag = self.i18n["ai_trans"]
                        elif zh_node.find('leon'): prefix_tag = self.i18n["proofread"]
                    zh_txt = zh_node.get_text(strip=True) if zh_node else ""
                    if zh_txt and prefix_tag: zh_txt = prefix_tag + zh_txt
                    if zh_node: zh_node.decompose()
                    self._mark_rich_text(ex)
                    panel_data["data"].append({"en": self.clean_text(ex.get_text()), "zh": zh_txt})

            elif utype == 'mlt':
                for ul in c_root.find_all('ul'):
                    items = [self.clean_text(li.get_text()) for li in ul.find_all('li')]
                    if items: panel_data["data"].append(items)
            else:
                # 💡 新增：收集无法精准解析的面板统计
                panel_data["data"] = self.clean_text(c_root.get_text())
                self.stats["fallback"][utype] = self.stats["fallback"].get(utype, 0) + 1

            if utype and utype not in self.stats["fallback"]:
                self.stats["vip_parsed"][utype] = self.stats["vip_parsed"].get(utype, 0) + 1
        except Exception as e:
            panel_data["data"] = self.clean_text(c_root.get_text())
            self.stats["errors"][utype] = self.stats["errors"].get(utype, 0) + 1

        return panel_data

    def parse_entry(self, html_content, word_list):
        word = word_list[0]
        aliases = [w for w in word_list if w != word]

        soup = BeautifulSoup(html_content, 'html.parser')

        if self.mode == "mono":
            for zh_tag in soup.find_all(['chn', 'deft', 'uset', 'xt', 'ubx', 'unxt', 'undt']):
                if zh_tag.find_parent('unboxx'):
                    continue
                zh_tag.decompose()

        entry_blocks = soup.find_all('div', class_='entry')
        if not entry_blocks: entry_blocks = soup.find_all('span', class_='idm-g')
        if not entry_blocks: return []

        results = []
        for entry_block in entry_blocks:
            entry_ir = {
                "word": word, "aliases": aliases, "pos": "", "phonetics": {"uk": "", "us": ""},
                "labels": [], "senses": [], "panels": [], "variants": [], "derivatives": [],
                "global_see_also": [], "phrasal_verbs_links": []
            }

            pos_node = entry_block.find('span', class_='pos')
            entry_ir["pos"] = pos_node.get_text(strip=True) if pos_node else ""

            uk_phon = entry_block.find('div', class_='phons_br')
            us_phon = entry_block.find('div', class_='phons_n_am')
            if uk_phon and uk_phon.find('span', class_='phon'): entry_ir["phonetics"]["uk"] = uk_phon.find('span', class_='phon').get_text(strip=True)
            if us_phon and us_phon.find('span', class_='phon'): entry_ir["phonetics"]["us"] = us_phon.find('span', class_='phon').get_text(strip=True)

            top_g = entry_block.find('div', class_='top-g')
            if not top_g: top_g = entry_block.find('div', class_='webtop')

            # Only word-head symbols belong in top-level Yomitan tags. Sense symbols are rendered per sense.
            for symbols_div in (top_g.find_all('div', class_='symbols') if top_g else []):
                for span in symbols_div.find_all('span'):
                    for cls in span.get('class', []):
                        if cls.startswith('ox3ksym_') or cls.startswith('ox3ksymsub_'):
                            entry_ir["labels"].extend(["Oxford3000", cls.split('_')[-1].upper()])
                        elif cls.startswith('ox5ksym_') or cls.startswith('ox5ksymsub_'):
                            entry_ir["labels"].extend(["Oxford5000", cls.split('_')[-1].upper()])
                        elif 'opal_symbol' in cls:
                            entry_ir["labels"].append("OPAL")
            entry_ir["labels"] = list(dict.fromkeys(entry_ir["labels"]))

            global_grammar = []
            if top_g:
                for v in top_g.find_all(['span', 'div'], class_=['variants', 'v-g', 'inflections', 'inflected_form']):
                    chn = v.find('chn')
                    chn_txt = chn.get_text(strip=True) if chn else ""
                    if chn: chn.decompose()
                    v_txt = self.clean_text(v.get_text())
                    if v_txt: entry_ir["variants"].append(f"{v_txt} {chn_txt}".strip())
                    v.decompose()

                for gram in top_g.find_all('span', class_=['grammar', 'labels', 'dis-g', 'use', 'subj', 'belong-to']):
                    chn = gram.find('chn')
                    chn_txt = chn.get_text(strip=True) if chn else ""
                    if chn: chn.decompose()
                    eng_txt = self.clean_text(gram.get_text())

                    eng_clean = re.sub(r'[()\[\]]', '', eng_txt).strip()
                    chn_clean = re.sub(r'[()\[\]]', '', chn_txt).strip()

                    if eng_clean:
                        gram_item = {"en": eng_clean, "zh": chn_clean}
                        if gram_item not in global_grammar:
                            global_grammar.append(gram_item)
                    gram.decompose()

            for ndv in entry_block.find_all(['span', 'a'], class_='ndv'):
                if ndv.find_parent(['span', 'li'], class_=['def', 'x', 'unx', 'p', 'gloss']):
                    continue

                container = ndv.find_parent('span', class_=['idm-g', 'run-on', 'xr-g'])
                if not container:
                    continue
                if getattr(container, '_ndv_processed', False): continue
                if container: container._ndv_processed = True

                chn = container.find('chn') if container else None
                chn_txt = chn.get_text(strip=True) if chn else ""
                if chn: chn.decompose()

                en_txt = self.clean_text(container.get_text() if container else ndv.get_text())
                if en_txt: entry_ir["derivatives"].append({"en": en_txt, "zh": chn_txt})
                if container and container.name != 'div': container.decompose()

            for wo in entry_block.find_all('span', class_='unbox', unbox='wordorigin'):
                panel_data = self._parse_panel(wo)
                entry_ir["panels"].append(panel_data)
                wo.decompose()

            for sense in entry_block.find_all('li', class_='sense'):
                sense_data = {
                    "shortcut": {}, "idiom": "", "phrasal_verb": "", "pattern": "",
                    "variants": [],
                    "grammar": global_grammar.copy(),
                    "eng": "", "chn": "", "examples": [],
                    "see_also": [], "panels": []
                }

                shcut_g = sense.find_parent(['span', 'div'], class_='shcut-g')
                if shcut_g:
                    shcut_node = shcut_g.find(['span', 'h2'], class_='shcut')
                    if shcut_node:
                        chn_node = shcut_node.find(['shcut', 'chn'])
                        chn_txt = chn_node.get_text(strip=True) if chn_node else ""
                        if chn_node: chn_node.decompose()
                        en_txt = self.clean_text(shcut_node.get_text())
                        sense_data["shortcut"] = {"en": en_txt, "zh": chn_txt}

                idm_g = sense.find_parent('span', class_='idm-g')
                if idm_g and idm_g.find('span', class_='idm'): sense_data["idiom"] = self.clean_text(idm_g.find('span', class_='idm').get_text())

                pv_g = sense.find_parent('span', class_='pv-g')
                if pv_g and pv_g.find('span', class_='pv'): sense_data["phrasal_verb"] = self.clean_text(pv_g.find('span', class_='pv').get_text())

                for variant in sense.find_all(['div', 'span'], class_='variants'):
                    zh_parts = []
                    for labelx in variant.find_all('labelx'):
                        zh_text = labelx.get_text(strip=True)
                        if zh_text:
                            zh_parts.append(zh_text)
                        labelx.decompose()
                    en_txt = self.clean_text(variant.get_text())
                    if en_txt:
                        variant_data = {"en": en_txt, "zh": "；".join(dict.fromkeys(zh_parts))}
                        if variant_data not in sense_data["variants"]:
                            sense_data["variants"].append(variant_data)
                    variant.decompose()

                topic_nodes = sense.find_all('span', class_='topic-g')
                for topic in topic_nodes:
                    topic_names = topic.find_all('span', class_='topic_name')
                    topic_cefrs = topic.find_all('span', class_='topic_cefr')
                    if topic_names:
                        for t_name, t_cefr in zip(topic_names, topic_cefrs):
                            name_str = t_name.get_text(strip=True)
                            cefr_str = t_cefr.get_text(strip=True).upper()
                            topic_tag = {"en": f"Topic: {name_str}", "zh": ""}
                            if cefr_str: topic_tag["en"] += f" ({cefr_str})"
                            if topic_tag not in sense_data["grammar"]:
                                sense_data["grammar"].append(topic_tag)
                    else:
                        for t_cefr in topic_cefrs:
                            cefr_str = t_cefr.get_text(strip=True).upper()
                            if not cefr_str:
                                continue
                            level_tag = {"en": f"CEFR: {cefr_str}", "zh": ""}
                            if level_tag not in sense_data["grammar"]:
                                sense_data["grammar"].append(level_tag)
                    topic.decompose()

                cf_nodes = sense.find_all('span', class_=['cf', 'patterns'])
                sense_cfs = []
                for cf in cf_nodes:
                    if cf.find_parent('ul', class_='examples'): continue
                    if cf.find_parent('span', class_='unbox'): continue
                    sense_cfs.append(self.clean_text(cf.get_text()))
                    cf.decompose()
                if sense_cfs:
                    sense_data["pattern"] = " | ".join(sense_cfs)

                for xref in sense.find_all('span', class_='xrefs'):
                    if xref.find_parent('span', class_='unbox'): continue
                    prefix_node = xref.find('span', class_='prefix')
                    prefix_txt = prefix_node.get_text(strip=True) if prefix_node else "See also"
                    prefix_txt = prefix_txt[0].upper() + prefix_txt[1:] if prefix_txt else "See also:"
                    if not prefix_txt.endswith(':'): prefix_txt += ':'
                    refs = []
                    for ref in xref.find_all('a', class_='Ref'):
                        xh = ref.find('span', class_='xh')
                        if xh: refs.append(xh.get_text(strip=True))
                        else: refs.append(ref.get_text(strip=True))
                    if refs: sense_data["see_also"].append({"type": prefix_txt, "links": refs})
                    xref.decompose()

                for unbox in sense.find_all('span', class_='unbox', unbox=True):
                    panel_data = self._parse_panel(unbox)
                    sense_data["panels"].append(panel_data)
                    unbox.decompose()

                meta_nodes = sense.find_all('span', class_=['grammar', 'labels', 'dis-g', 'use', 'subj', 'belong-to'])
                if idm_g:
                    for gram in idm_g.find_all('span', class_=['grammar', 'labels', 'dis-g', 'use', 'subj', 'belong-to']):
                        if not gram.find_parent('li', class_='sense'): meta_nodes.insert(0, gram)

                seen_gram = []
                for gram in meta_nodes:
                    if not gram.find_parent('span', class_='unbox') and not gram.find_parent('ul', class_='examples'):
                        chn = gram.find('chn')
                        chn_txt = chn.get_text(strip=True) if chn else ""
                        if chn: chn.decompose()
                        eng_txt = self.clean_text(gram.get_text())

                        eng_clean = re.sub(r'[()\[\]]', '', eng_txt).strip()
                        chn_clean = re.sub(r'[()\[\]]', '', chn_txt).strip()

                        if eng_clean:
                            gram_item = {"en": eng_clean, "zh": chn_clean}
                            if gram_item not in sense_data["grammar"]:
                                sense_data["grammar"].append(gram_item)
                        gram.decompose()

                def_tag = sense.find('span', class_='def')
                deft_tag = sense.find('deft')
                if def_tag:
                    self._mark_rich_text(def_tag)
                    sense_data["eng"] = self.clean_text(def_tag.get_text())
                if deft_tag:
                    for ai in deft_tag.find_all('ai'): ai.replace_with(ai.get_text())
                    sense_data["chn"] = self.clean_text(deft_tag.get_text())

                ex_list = []
                ex_ul = sense.find('ul', class_='examples')
                if ex_ul:
                    for ex_li in ex_ul.find_all('li'):
                        # Keep example-level construction labels with the example text.
                        li_cf_tags = ex_li.find_all('span', class_='cf', recursive=False)
                        cf_prefix = ""
                        if li_cf_tags:
                            cf_prefix = f"[{' | '.join([self.clean_text(c.get_text()) for c in li_cf_tags])}] "
                            for c in li_cf_tags: c.decompose()

                        ex_span = ex_li.find('span', class_=['x', 'unx'])
                        if ex_span:
                            chn_node = ex_span.find(['unxt', 'chn', 'xt'])
                            q_score = 0
                            prefix_tag = ""
                            if chn_node:
                                if chn_node.find('ai'):
                                    q_score = 2
                                    prefix_tag = self.i18n["ai_trans"]
                                elif chn_node.find('leon'):
                                    q_score = 1
                                    prefix_tag = self.i18n["proofread"]
                            ex_chn = chn_node.get_text(strip=True) if chn_node else ""
                            if ex_chn and prefix_tag: ex_chn = prefix_tag + ex_chn
                            if chn_node: chn_node.decompose()

                            self._mark_rich_text(ex_span)
                            ex_eng = self.clean_text(ex_span.get_text())
                            ex_list.append({"en": cf_prefix + ex_eng, "zh": ex_chn, "score": q_score})

                if ex_list:
                    ex_list.sort(key=lambda x: x["score"])
                    sense_data["examples"] = [{"en": ex["en"], "zh": ex["zh"]} for ex in ex_list[:5]]

                entry_ir["senses"].append(sense_data)

            for xref in entry_block.find_all('span', class_='xrefs'):
                if xref.find_parent('span', class_='unbox'): continue
                prefix_node = xref.find('span', class_='prefix')
                prefix_txt = prefix_node.get_text(strip=True) if prefix_node else "See also"
                prefix_txt = prefix_txt[0].upper() + prefix_txt[1:] if prefix_txt else "See also:"
                if not prefix_txt.endswith(':'): prefix_txt += ':'
                refs = []
                for ref in xref.find_all('a', class_='Ref'):
                    xh = ref.find('span', class_='xh')
                    if xh: refs.append(xh.get_text(strip=True))
                    else: refs.append(ref.get_text(strip=True))
                if refs: entry_ir["global_see_also"].append({"type": prefix_txt, "links": refs})
                xref.decompose()

            pv_aside = entry_block.find('aside', class_='phrasal_verb_links')
            if pv_aside:
                entry_ir["phrasal_verbs_links"] = [self.clean_text(xh.get_text()) for xh in pv_aside.find_all('span', class_='xh')]
                pv_aside.decompose()

            for unbox in entry_block.find_all('span', class_='unbox', unbox=True):
                panel_data = self._parse_panel(unbox)
                entry_ir["panels"].append(panel_data)

            results.append(entry_ir)

        return results

# ==========================================
# Module 2: Yomitan Renderer
# ==========================================
class YomitanRenderer:
    def __init__(self, mode="bilingual", ui_lang="zh", open_panels=False):
        self.mode = mode
        self.ui_lang = ui_lang
        self.i18n = I18N_TEXT[ui_lang]
        self.open_panels = open_panels

    def _structured_definition(self, content):
        return [{
            "type": "structured-content",
            "content": sanitize_structured_content(content, allow_open=self.open_panels)
        }]

    def _shortcut_key(self, sense):
        shortcut = sense.get("shortcut") or {}
        en = normalize_label(shortcut.get("en", "")).casefold()
        zh = normalize_label(shortcut.get("zh", "")).casefold()
        return en or zh

    def _sense_has_visible_content(self, sense):
        visible_panels = [panel for panel in sense.get("panels", []) if panel.get("data")]
        return bool(
            sense.get("eng")
            or sense.get("chn")
            or sense.get("examples")
            or sense.get("see_also")
            or visible_panels
        )

    def _wrap_sense_header(self, content):
        if not content:
            return content
        first = content[0]
        if not (isinstance(first, dict) and (first.get("data") or {}).get("class") == "oald-def-num"):
            return content

        body = list(content[1:])
        while body and isinstance(body[0], str) and not body[0].strip():
            body.pop(0)
        return [
            first,
            {"tag": "span", "data": {"class": "oald-head-main"}, "content": body},
        ]

    def _sense_header_node(self, content):
        first = content[0] if content else None
        numbered = isinstance(first, dict) and (first.get("data") or {}).get("class") == "oald-def-num"
        return {
            "tag": "div",
            "data": {"class": "oald-sense-header-numbered" if numbered else "oald-sense-header"},
            "content": self._wrap_sense_header(content) if numbered else content,
        }

    def render_link_block(self, label, links):
        clean_links = [link for link in links if link]
        if not clean_links:
            return None

        clean_label = format_xref_label(label, self.ui_lang)
        content = [{"tag": "span", "data": {"class": "oald-cross-ref-icon"}, "content": "➔\u00A0"}]
        if clean_label:
            content.append({
                "tag": "span",
                "data": {"class": "oald-label"},
                "lang": self.ui_lang,
                "content": f"{clean_label}:\u00A0"
            })

        for i, link in enumerate(clean_links):
            content.append({"tag": "a", "href": f"?query={link}&wildcards=off", "content": link})
            if i < len(clean_links) - 1:
                content.append(", ")

        return {"tag": "div", "data": {"class": "oald-link"}, "content": content}

    def render_rich_text(self, text, prefix=""):
        if '⚑' not in text and '★' not in text:
            return prefix + text if prefix or text else ""

        content = []
        if prefix: content.append({"tag": "span", "content": prefix})
        parts = re.split(r'(⚑.*?⚐|★.*?☆)', text)
        for part in parts:
            if part.startswith('⚑') and part.endswith('⚐'):
                inner_text = part[1:-1]
                if inner_text: content.append({"tag": "span", "data": {"class": "oald-bold"}, "content": inner_text})
            elif part.startswith('★') and part.endswith('☆'):
                inner_text = part[1:-1]
                if inner_text: content.append({"tag": "span", "data": {"class": "oald-gloss"}, "content": f" {inner_text} "})
            elif part:
                if part.strip() or part == " ":
                    content.append({"tag": "span", "content": part})

        if len(content) == 1 and isinstance(content[0], str): return content[0]
        return content if content else ""

    def _is_redundant(self, shcut, gram):
        if not shcut or not shcut.get('zh') or not gram.get('zh'): return False
        zh_sh = "".join(re.findall(r'[\u4e00-\u9fff]+', shcut['zh']))
        zh_gr = "".join(re.findall(r'[\u4e00-\u9fff]+', gram['zh']))
        return bool(zh_sh and zh_gr and zh_sh in zh_gr)

    def _is_redundant_pattern(self, shcut, pattern):
        if not shcut or not shcut.get('en') or not pattern: return False
        sh_en = shcut['en'].lower()
        pat_clean = re.sub(r'[()\[\]]', '', pattern).lower().strip()
        return bool(pat_clean and sh_en and (pat_clean in sh_en or sh_en in pat_clean))

    def render_ex_pair(self, en_text, zh_text=None, is_panel=False):
        sym = "▪\u00A0" if self.mode == "mono" else "▼\u00A0"
        en_class = f"oald-{'panel-' if is_panel else ''}ex-en"

        en_content = [{"tag": "span", "data": {"class": "oald-sym"}, "content": sym}]

        # Highlight one or more example patterns only when they appear at the beginning.
        match = re.match(r'^\s*((?:\[[^\]]+\]\s*)+)(.*)', en_text)
        if match:
            pattern_texts = re.findall(r'\[[^\]]+\]', match.group(1))
            rest_text = match.group(2).lstrip()
            for pattern_text in pattern_texts:
                en_content.append({"tag": "span", "data": {"class": "oald-ex-pattern"}, "content": f"{pattern_text} "})
            if rest_text:
                en_rich = self.render_rich_text(rest_text)
                if isinstance(en_rich, list): en_content.extend(en_rich)
                else: en_content.append(en_rich)
        else:
            en_rich = self.render_rich_text(en_text)
            if isinstance(en_rich, list): en_content.extend(en_rich)
            else: en_content.append(en_rich)

        blocks = [{"tag": "div", "data": {"class": en_class}, "content": en_content}]

        if zh_text:
            zh_class = f"oald-{'panel-' if is_panel else ''}ex-zh"
            zh_content = [{"tag": "span", "data": {"class": "oald-sym"}, "content": "└\u00A0"}]
            zh_rich = self.render_rich_text(zh_text)
            if isinstance(zh_rich, list): zh_content.extend(zh_rich)
            else: zh_content.append(zh_rich)
            blocks.append({"tag": "div", "lang": "zh", "data": {"class": zh_class}, "content": zh_content})

        return blocks

    def render_bullet(self, text):
        en_content = [{"tag": "span", "data": {"class": "oald-sym"}, "content": "•\u00A0"}]
        en_rich = self.render_rich_text(text)
        if isinstance(en_rich, list): en_content.extend(en_rich)
        else: en_content.append(en_rich)
        return {"tag": "div", "data": {"class": "oald-ex-en"}, "content": en_content}

    def render_unbox(self, panel):
        title = f"{panel['title_en']} {panel['title_zh']}".strip()
        blocks = []
        utype = panel['type']
        data = panel['data']

        if not data: return None
        if isinstance(data, str):
            blocks.append({"tag": "div", "content": data})

        elif utype == 'wordorigin':
            if isinstance(data, dict):
                if data.get('en'): blocks.append({"tag": "div", "content": self.render_rich_text(data['en'])})
                if data.get('zh'): blocks.append({"tag": "div", "lang": "zh", "content": data['zh']})

        elif utype == 'cult' or utype == 'extra_examples':
            for item in data:
                blocks.extend(self.render_ex_pair(item['en'], item.get('zh'), is_panel=True))

        elif utype == 'verbforms':
            rows = []
            for item in data:
                phon_str = ""
                if item['phonetics'].get('uk') and item['phonetics'].get('uk') == item['phonetics'].get('us'): phon_str = f"UK/US: {item['phonetics']['uk']}"
                else: phon_str = " | ".join([f"{k.upper()}: {v}" for k, v in item['phonetics'].items() if v])
                rows.append({"tag": "tr", "content": [
                    {"tag": "td", "content": f"{item['form']}   "},
                    {"tag": "td", "data": {"class": "oald-bold"}, "content": f"{item['word']}   "},
                    {"tag": "td", "content": phon_str}
                ]})
            blocks.append({"tag": "table", "content": [{"tag": "tbody", "content": rows}]})

        elif utype == 'synonyms':
            if data['intro_en']: blocks.append({"tag": "div", "content": self.render_rich_text(data['intro_en'])})
            if data['intro_zh']: blocks.append({"tag": "div", "lang": "zh", "content": data['intro_zh']})
            for item in data['items']:
                line = []
                if item['highlight']: line.append({"tag": "span", "data": {"class": "oald-bold"}, "content": f"{item['highlight']} "})
                if item['en']: line.append({"tag": "span", "content": item['en']})
                blocks.append({"tag": "div", "content": line})
                if item['zh']: blocks.append({"tag": "div", "lang": "zh", "content": item['zh']})

                ex_blocks = []
                for ex in item['examples']:
                    ex_blocks.extend(self.render_ex_pair(ex['en'], ex.get('zh'), is_panel=True))
                if ex_blocks: blocks.append({"tag": "div", "data": {"class": "oald-panel-indent"}, "content": ex_blocks})

        elif utype in ['langbank', 'which_word', 'british_american', 'wordfinder', 'wordfamily', 'grammar', 'more_about', 'express', 'vocab']:
            for sec in data:
                header = f"{sec['subtitle_en']} {sec['subtitle_zh']}".strip()
                if header: blocks.append({"tag": "div", "lang": "zh", "data": {"class": "oald-group"}, "content": header})
                for item in sec['items']:
                    if item['en']: blocks.append({"tag": "div", "content": f"■ {item['en']}"})
                    if item['zh']: blocks.append({"tag": "div", "lang": "zh", "content": item['zh']})

                    ex_blocks = []
                    for ex in item['examples']:
                        ex_blocks.extend(self.render_ex_pair(ex['en'], ex.get('zh'), is_panel=True))
                    if ex_blocks: blocks.append({"tag": "div", "data": {"class": "oald-panel-indent"}, "content": ex_blocks})

        elif utype == 'colloc':
            for sec in data:
                header = sec['group_en']
                if sec['group_zh'] and sec['group_zh'] != sec['group_en']: header += f" ({sec['group_zh']})"
                if header: blocks.append({"tag": "div", "lang": "zh", "data": {"class": "oald-group"}, "content": header})
                for item in sec['items']:
                    blocks.append(self.render_bullet(item['en']))
                    if item['zh']: blocks.append(self.render_bullet(item['zh']))

        elif utype == 'homophone':
            for item in data:
                pos_str = f" {item['pos_info']}" if item.get('pos_info') else ""
                blocks.append({"tag": "div", "content": [
                    {"tag": "span", "data": {"class": "oald-bold"}, "content": f"• {item['word']}"},
                    {"tag": "span", "content": pos_str}
                ]})
                ex_blocks = []
                if item.get('example_en'):
                     ex_blocks.extend(self.render_ex_pair(item['example_en'], item.get('example_zh'), is_panel=True))
                if ex_blocks:
                     blocks.append({"tag": "div", "data": {"class": "oald-panel-indent"}, "content": ex_blocks})

        elif utype == 'snippet':
            if isinstance(data, list):
                for sec in data: blocks.append({"tag": "div", "content": f"[{sec['title']}] {', '.join(sec['items'])}"})
        elif utype == 'mlt':
            if isinstance(data, list):
                for items in data: blocks.append({"tag": "div", "content": f"• {', '.join(items)}"})

        node = {
            "tag": "details",
            "data": {"class": "oald-panel"},
            "content": [
                {"tag": "summary", "lang": self.ui_lang, "data": {"class": "oald-panel-title"}, "content": title},
                {"tag": "div", "data": {"class": "oald-panel-content"}, "content": blocks}
            ]
        }
        if self.open_panels:
            node["open"] = True
        return node

    def render_entry(self, entry_ir):
        content_blocks = []

        # 头部发音与变体
        phon_str = ""
        if entry_ir['phonetics'].get('uk') and entry_ir['phonetics'].get('uk') == entry_ir['phonetics'].get('us'):
            phon_str = f"UK/US: {entry_ir['phonetics']['uk']}"
        else:
            phon_str = " | ".join([f"{k.upper()}: {v}" for k, v in entry_ir['phonetics'].items() if v])

        if phon_str:
            content_blocks.append({"tag": "div", "data": {"class": "oald-phonetics"}, "content": f"🔈 {phon_str}"})

        if entry_ir.get('variants'):
            for v in entry_ir['variants']:
                content_blocks.append({"tag": "div", "data": {"class": "oald-variant"}, "content": v})

        senses = [sense for sense in entry_ir['senses'] if self._sense_has_visible_content(sense)]
        last_shortcut_key = ""
        for i, sense in enumerate(senses):

            prefix = (f"{chr(0x2460 + i)}" if i < 20 else f"({i+1})") if len(senses) > 1 else ""
            prefix_node = {"tag": "span", "data": {"class": "oald-def-num"}, "content": f"{prefix}\u00A0"} if prefix else None

            sense_class = "oald-sense" if prefix else "oald-sense-single"
            sense_container = {"tag": "div", "data": {"class": sense_class}, "content": []}

            # 👑 全新的极简行内头部 (Inline Span Flow)：完美应对复制和排版
            header_content = []
            has_header_detail = False

            if prefix_node:
                header_content.append(prefix_node)

            shortcut_key = self._shortcut_key(sense)

            for variant in sense.get("variants", []):
                variant_content = [{"tag": "span", "content": variant["en"]}]
                if variant.get("zh"):
                    variant_content.append({"tag": "span", "content": "\u00A0"})
                    variant_content.append({"tag": "span", "lang": "zh", "content": variant["zh"]})
                header_content.append({"tag": "span", "data": {"class": "oald-variant-inline"}, "content": variant_content})
                header_content.append(" ")
                has_header_detail = True

            if sense['idiom']:
                header_content.append({"tag": "span", "lang": "zh", "data": {"class": "oald-idiom-title"}, "content": f"♦\u00A0{sense['idiom']}"})
                header_content.append(" ")
                has_header_detail = True
                last_shortcut_key = ""
            elif sense['shortcut'] and shortcut_key != last_shortcut_key:
                sh_content = [{"tag": "span", "content": sense['shortcut']['en']}]
                if sense['shortcut']['zh']:
                    sh_content.append({"tag": "span", "content": "\u00A0"})
                    sh_content.append({"tag": "span", "lang": "zh", "content": sense['shortcut']['zh']})
                header_content.append({"tag": "span", "data": {"class": "oald-shortcut"}, "content": sh_content})
                header_content.append(" ")
                has_header_detail = True
                last_shortcut_key = shortcut_key
            elif not sense['shortcut']:
                last_shortcut_key = ""

            filtered_grammar = []
            for g in sense['grammar']:
                if self._is_redundant(sense['shortcut'], g): continue
                filtered_grammar.append(g)

            if sense['phrasal_verb']:
                header_content.append({"tag": "span", "data": {"class": "oald-tag-grammar"}, "content": sense['phrasal_verb']})
                header_content.append(" ")
                has_header_detail = True

            for gram in filtered_grammar:
                is_topic_tag = gram['en'].startswith('Topic:')
                tag_class = "oald-tag-topic" if is_topic_tag else "oald-tag-grammar"
                if is_topic_tag:
                    clean_en = gram['en'].replace('Topic: ', '').upper()
                elif gram['en'].startswith('CEFR:'):
                    clean_en = gram['en'].replace('CEFR: ', '').upper()
                else:
                    clean_en = gram['en']
                if tag_class == "oald-tag-grammar" and len(clean_en) > 28:
                    tag_class = "oald-tag-grammar-long"

                tag_inner = [{"tag": "span", "content": clean_en}]
                if gram['zh']:
                    tag_inner.append({"tag": "span", "content": "\u00A0"})
                    tag_inner.append({"tag": "span", "lang": "zh", "content": gram['zh']})

                header_content.append({"tag": "span", "data": {"class": tag_class}, "content": tag_inner})
                header_content.append(" ")
                has_header_detail = True

            if sense['pattern'] and not self._is_redundant_pattern(sense['shortcut'], sense['pattern']):
                header_content.append({"tag": "span", "data": {"class": "oald-pattern"}, "content": f"[{sense['pattern']}]"})
                has_header_detail = True

            eng_in_header = bool(prefix_node and sense['eng'] and not has_header_detail)
            chn_in_header = False
            pending_prefix = []
            if eng_in_header:
                eng_rich = self.render_rich_text(sense['eng'])
                if isinstance(eng_rich, list): header_content.extend(eng_rich)
                else: header_content.append(eng_rich)
            elif prefix_node and sense['chn'] and not has_header_detail:
                header_content.append({"tag": "span", "lang": "zh", "content": sense['chn']})
                chn_in_header = True
            elif prefix_node and not has_header_detail:
                pending_prefix = header_content
                header_content = []

            if header_content:
                sense_container["content"].append(self._sense_header_node(header_content))

            # 👑 正文与例句块
            if sense['eng'] and not eng_in_header:
                sense_container["content"].append({"tag": "div", "data": {"class": "oald-eng"}, "content": self.render_rich_text(sense['eng'])})

            if sense['chn'] and not chn_in_header:
                sense_container["content"].append({"tag": "div", "lang": "zh", "data": {"class": "oald-chn"}, "content": sense['chn']})

            for ex in sense['examples']:
                sense_container["content"].extend(self.render_ex_pair(ex['en'], ex.get('zh')))

            if sense.get('see_also'):
                for sa in sense['see_also']:
                    node = self.render_link_block(sa.get('type'), sa.get('links', []))
                    if node:
                        if pending_prefix and isinstance(node.get("content"), list):
                            node["content"] = pending_prefix + node["content"]
                            pending_prefix = []
                        sense_container["content"].append(node)

            if sense.get('panels'):
                for p in sense['panels']:
                    node = self.render_unbox(p)
                    if node: sense_container["content"].append(node)

            if pending_prefix:
                sense_container["content"].append(self._sense_header_node(pending_prefix))

            content_blocks.append(sense_container)

        # 👑 底部全局交叉引用与衍生词
        if entry_ir['global_see_also']:
            for sa in entry_ir['global_see_also']:
                node = self.render_link_block(sa.get('type'), sa.get('links', []))
                if node:
                    content_blocks.append(node)

        if entry_ir['phrasal_verbs_links']:
            node = self.render_link_block("Phrasal verbs", entry_ir['phrasal_verbs_links'])
            if node:
                content_blocks.append(node)

        if entry_ir['panels']:
            for p in entry_ir['panels']:
                node = self.render_unbox(p)
                if node: content_blocks.append(node)

        if entry_ir.get('derivatives'):
            for drv in entry_ir['derivatives']:
                drv_content = [{"tag": "span", "data": {"class": "oald-derivative-word"}, "content": f"► {drv['en']}"}]
                if drv['zh']: drv_content.append({"tag": "span", "lang": "zh", "content": f"  {drv['zh']}"})
                content_blocks.append({"tag": "div", "data": {"class": "oald-derivative"}, "content": drv_content})

        return self._structured_definition({"tag": "div", "content": content_blocks})


# ==========================================
# Module 3: Packaging & Control Flow
# ==========================================
def get_dictionary_title(mode, ui_lang, debug_mode=False):
    base_title = "OALD 10"
    if debug_mode:
        base_title += f" (Test_{int(time.time())})"

    if mode == "mono" and ui_lang == "en": return f"{base_title} (Global)"
    elif mode == "mono" and ui_lang == "zh": return f"{base_title} (Immersion)"
    elif mode == "bilingual" and ui_lang == "en": return f"{base_title} (EN Tags)"
    else: return base_title

def generate_metadata_files(output_dir, mode, ui_lang, debug_mode=False):
    i18n = I18N_TEXT[ui_lang]
    index_data = {
        "title": get_dictionary_title(mode, ui_lang, debug_mode=debug_mode),
        "format": 3, "revision": f"v{VERSION}", "sequenced": True, "author": AUTHOR,
        "description": i18n["desc_mono"] if mode == "mono" else i18n["desc_bilingual"]
    }
    with open(os.path.join(output_dir, 'index.json'), 'w', encoding='utf-8') as f:
        if debug_mode: json.dump(index_data, f, ensure_ascii=False, indent=2)
        else: json.dump(index_data, f, ensure_ascii=False, separators=(',', ':'))

    tags = i18n["tags"]
    tag_data = [
        ["noun", "partOfSpeech", 1, tags["noun"], 0], ["verb", "partOfSpeech", 1, tags["verb"], 0],
        ["adj", "partOfSpeech", 1, tags["adj"], 0], ["adv", "partOfSpeech", 1, tags["adv"], 0],
        ["pron", "partOfSpeech", 1, tags["pron"], 0], ["prep", "partOfSpeech", 1, tags["prep"], 0],
        ["conj", "partOfSpeech", 1, tags["conj"], 0], ["excl", "partOfSpeech", 1, tags["excl"], 0],
        ["det", "partOfSpeech", 1, tags["det"], 0], ["def-article", "partOfSpeech", 1, tags["def-article"], 0],
        ["indef-article", "partOfSpeech", 1, tags["indef-article"], 0], ["num", "partOfSpeech", 1, tags["num"], 0],
        ["ordinal-num", "partOfSpeech", 1, tags["ordinal-num"], 0], ["modal", "partOfSpeech", 1, tags["modal"], 0],
        ["aux", "partOfSpeech", 1, tags["aux"], 0], ["linking-v", "partOfSpeech", 1, tags["linking-v"], 0],
        ["phrasal-v", "partOfSpeech", 1, tags["phrasal-v"], 0], ["prefix", "partOfSpeech", 1, tags["prefix"], 0],
        ["suffix", "partOfSpeech", 1, tags["suffix"], 0], ["combining-form", "partOfSpeech", 1, tags["combining-form"], 0],
        ["inf-marker", "partOfSpeech", 1, tags["inf-marker"], 0], ["short-form", "partOfSpeech", 1, tags["short-form"], 0],
        ["abbr", "partOfSpeech", 1, tags["abbr"], 0], ["noun/adj", "partOfSpeech", 1, tags["noun/adj"], 0],
        ["idiom", "expression", 1, tags["idiom"], 0], ["symb", "partOfSpeech", 1, tags["symb"], 0],
        ["A1", "frequent", 2, tags["A1"], 0], ["A2", "frequent", 2, tags["A2"], 0],
        ["B1", "frequent", 2, tags["B1"], 0], ["B2", "frequent", 2, tags["B2"], 0],
        ["C1", "frequent", 2, tags["C1"], 0], ["C2", "frequent", 2, tags["C2"], 0],
        ["Oxford3000", "popular", 3, tags["Oxford3000"], 0], ["Oxford5000", "popular", 3, tags["Oxford5000"], 0],
        ["OPAL", "popular", 3, tags["OPAL"], 0], ["redirect", "search", -5, tags["redirect"], 0]
    ]
    with open(os.path.join(output_dir, 'tag_bank_1.json'), 'w', encoding='utf-8') as f:
        if debug_mode: json.dump(tag_data, f, ensure_ascii=False, indent=2)
        else: json.dump(tag_data, f, ensure_ascii=False, separators=(',', ':'))


def walk_structured_content(value):
    if isinstance(value, dict):
        yield value
        for item in value.values():
            yield from walk_structured_content(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk_structured_content(item)


def structured_text(value):
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "".join(structured_text(item) for item in value)
    if isinstance(value, dict):
        return structured_text(value.get("content", ""))
    return ""


def count_structured_key(value, key):
    if isinstance(value, dict):
        return (1 if key in value else 0) + sum(count_structured_key(item, key) for item in value.values())
    if isinstance(value, list):
        return sum(count_structured_key(item, key) for item in value)
    return 0


def validate_yomitan_zip(zip_path, mode, allow_open=False):
    required_files = {"index.json", "tag_bank_1.json", "styles.css"}
    stats = {
        "term_banks": 0,
        "rows": 0,
        "structured_rows": 0,
        "redirect_rows": 0,
        "open_keys": 0,
        "style_keys": 0,
        "blank_headers": 0,
    }
    errors = []

    with zipfile.ZipFile(zip_path, 'r') as zipf:
        names = set(zipf.namelist())
        missing = sorted(required_files - names)
        if missing:
            errors.append(f"missing required files: {', '.join(missing)}")

        term_banks = sorted(
            [name for name in names if re.fullmatch(r"term_bank_\d+\.json", name)],
            key=lambda name: int(re.search(r"\d+", name).group(0)),
        )
        stats["term_banks"] = len(term_banks)
        if not term_banks:
            errors.append("no term_bank_*.json files found")

        css = zipf.read("styles.css").decode("utf-8") if "styles.css" in names else ""
        expected_indent = "0.95em" if mode == "mono" else "1.35em"
        if expected_indent and f"padding-left: {expected_indent}" not in css:
            errors.append(f"styles.css does not contain expected example indent {expected_indent}")
        if "display: grid" in css or "text-indent: -1.18em" in css:
            errors.append("styles.css still contains obsolete sense-header layout rules")

        for bank_name in term_banks:
            try:
                bank_rows = json.loads(zipf.read(bank_name).decode("utf-8"))
            except Exception as exc:
                errors.append(f"{bank_name} is not valid JSON: {exc}")
                continue

            if not isinstance(bank_rows, list):
                errors.append(f"{bank_name} is not a JSON array")
                continue

            stats["rows"] += len(bank_rows)
            for idx, row in enumerate(bank_rows):
                if not isinstance(row, list) or len(row) < 6:
                    errors.append(f"{bank_name}[{idx}] is not a valid term row")
                    continue

                definitions = row[5]
                stats["open_keys"] += count_structured_key(definitions, "open")
                stats["style_keys"] += count_structured_key(definitions, "style")

                if isinstance(definitions, list) and definitions:
                    first_def = definitions[0]
                    if isinstance(first_def, dict) and first_def.get("type") == "structured-content":
                        stats["structured_rows"] += 1
                    elif isinstance(first_def, list):
                        stats["redirect_rows"] += 1

                for node in walk_structured_content(definitions):
                    node_class = (node.get("data") or {}).get("class")
                    if node_class in {"oald-sense-header", "oald-sense-header-numbered"}:
                        text = structured_text(node).strip()
                        if re.fullmatch(r"[①-⑳]|\(\d+\)", text):
                            stats["blank_headers"] += 1

    if stats["style_keys"]:
        errors.append(f"structured content contains {stats['style_keys']} unsupported style keys")
    if stats["open_keys"] and not allow_open:
        errors.append(f"structured content contains {stats['open_keys']} open keys")
    if stats["blank_headers"]:
        errors.append(f"found {stats['blank_headers']} blank sense headers")

    print("\n=== Package Validation ===")
    print(f"[*] Zip: {zip_path}")
    print(f"[*] Term Banks: {stats['term_banks']}")
    print(f"[*] Rows: {stats['rows']}")
    print(f"[*] Structured Rows: {stats['structured_rows']}")
    print(f"[*] Redirect Rows: {stats['redirect_rows']}")
    print(f"[*] open/style keys: {stats['open_keys']}/{stats['style_keys']}")
    print(f"[*] Blank Sense Headers: {stats['blank_headers']}")

    if errors:
        for error in errors:
            print(f"[ERROR] {error}")
        raise RuntimeError("Generated Yomitan package failed validation")

    print("[OK] Package validation passed")
    return stats


def package_dictionary(input_file, output_dir, mode, ui_lang, keep_json=False, open_panels=False,
                       debug_mode=False, test_words=None, validate=True):
    os.makedirs(output_dir, exist_ok=True)
    zip_filename = get_zip_filename(mode, ui_lang, debug_mode=debug_mode)
    cleanup_output_dir(output_dir, zip_filename=zip_filename)
    print(f"=== OALD 10 to Yomitan V{VERSION} Engine ===")
    print(f"[*] Mode: {mode}")
    print(f"[*] UI Language: {ui_lang}")
    print(f"[*] Debug Build: {debug_mode}")

    extractor = OaldExtractor(mode=mode, ui_lang=ui_lang)
    renderer = YomitanRenderer(mode=mode, ui_lang=ui_lang, open_panels=open_panels)
    debug_word_set = set(test_words or DEFAULT_TEST_WORDS)

    real_entries = {}
    redirects = {}
    parsed_html_entries = 0
    skipped_html_entries = 0
    redirect_aliases = 0
    generated_files = []

    with open(input_file, 'r', encoding='utf-8') as f: total_lines = sum(1 for _ in f)

    def process_entry_buffer(buf):
        nonlocal parsed_html_entries, skipped_html_entries, redirect_aliases
        entry_text = "\n".join(buf)
        lines = entry_text.split('\n')
        if len(lines) < 2: return
        words = [w.strip() for w in lines[0].split('|') if w.strip()]
        if debug_mode and not any(tw in words for tw in debug_word_set): return
        content = "".join(lines[1:])

        if "@@@LINK=" in content:
            target = content.replace("@@@LINK=", "").strip().split('|')[0].strip()
            for w in words:
                if w != target:
                    if w not in redirects: redirects[w] = []
                    redirects[w].append(target)
                    redirect_aliases += 1
        else:
            ir_list = extractor.parse_entry(content, words)
            if ir_list:
                parsed_html_entries += 1
                for w in words:
                    if w not in real_entries: real_entries[w] = []
                    real_entries[w].extend(ir_list)
            else:
                skipped_html_entries += 1

    with open(input_file, 'r', encoding='utf-8') as f:
        buffer = []
        for line in tqdm(f, total=total_lines, desc="Processing Data"):
            line = line.strip()
            if line == "</>":
                if buffer: process_entry_buffer(buffer)
                buffer = []
            else:
                buffer.append(line)
        if buffer: process_entry_buffer(buffer)

    resolved_redirects = {}
    for word, targets in redirects.items():
        valid_targets = []
        for t in targets:
            current_target = t
            visited = set([word])
            while current_target in redirects and current_target not in visited:
                visited.add(current_target)
                current_target = redirects[current_target][0]
            if current_target in real_entries and current_target != word: valid_targets.append(current_target)
        if valid_targets: resolved_redirects[word] = valid_targets

    term_bank, file_index, count = [], 1, 0

    def save_bank(data, idx):
        path = os.path.join(output_dir, f'term_bank_{idx}.json')
        with open(path, 'w', encoding='utf-8') as f:
            if debug_mode: json.dump(data, f, ensure_ascii=False, indent=2)
            else: json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
        generated_files.append(path)

    pos_mapping = {"verb": "v", "noun": "n", "adjective": "adj", "adverb": "adv", "pronoun": "pron", "preposition": "prep", "conjunction": "conj", "phrasal verb": "v_phr"}
    visual_tag_map = {"noun": "noun", "verb": "verb", "adjective": "adj", "adverb": "adv", "pronoun": "pron", "preposition": "prep", "conjunction": "conj", "exclamation": "excl", "determiner": "det", "definite article": "def-article", "indefinite article": "indef-article", "number": "num", "ordinal number": "ordinal-num", "modal verb": "modal", "auxiliary verb": "aux", "linking verb": "linking-v", "phrasal verb": "phrasal-v", "prefix": "prefix", "suffix": "suffix", "combining form": "combining-form", "infinitive marker": "inf-marker", "short form": "short-form", "abbreviation": "abbr", "idiom": "idiom", "symbol": "symb", "n.": "noun", "adj.": "adj", "n., adj.": "noun/adj"}

    global_unique_entries = {}
    for word, ir_list in real_entries.items():
        for ir in ir_list:
            ir_copy = ir.copy()
            ir_copy.pop('word', None)
            ir_copy.pop('aliases', None)
            ir_hash = json.dumps(ir_copy, sort_keys=True)
            if ir_hash not in global_unique_entries: global_unique_entries[ir_hash] = {"words": set(), "ir": ir}
            global_unique_entries[ir_hash]["words"].add(word)
            for alias in ir.get('aliases', []): global_unique_entries[ir_hash]["words"].add(alias)

    for ir_hash, data in global_unique_entries.items():
        ir = data["ir"]
        words = sorted(list(data["words"]))
        final_defs = renderer.render_entry(ir)
        term_tags = []
        raw_pos = ir['pos'].lower()
        if raw_pos in visual_tag_map: term_tags.append(visual_tag_map[raw_pos])
        elif raw_pos: term_tags.append(raw_pos.replace(" ", "-"))
        term_tags.extend(ir['labels'])
        rule_pos = pos_mapping.get(raw_pos, "")
        tags_str = " ".join(term_tags)

        for w in words:
            term_bank.append([w, "", tags_str, rule_pos, 10, final_defs, count, ""])
        count += 1
        if len(term_bank) >= 10000:
            save_bank(term_bank, file_index)
            term_bank = []
            file_index += 1

    for word, root_targets in resolved_redirects.items():
        if not root_targets: continue
        redirect_content = [[t, ["redirect"]] for t in list(dict.fromkeys(root_targets))]
        term_bank.append([word, "", "non-lemma", "", -10, redirect_content, count, ""])
        count += 1
        if len(term_bank) >= 10000:
            save_bank(term_bank, file_index)
            term_bank = []
            file_index += 1

    if term_bank: save_bank(term_bank, file_index)
    generate_metadata_files(output_dir, mode, ui_lang, debug_mode=debug_mode)
    generated_files.extend([
        os.path.join(output_dir, 'index.json'),
        os.path.join(output_dir, 'tag_bank_1.json'),
    ])

    css_path = os.path.join(output_dir, 'styles.css')
    with open(css_path, 'w', encoding='utf-8') as f:
        f.write(generate_css(mode))
    generated_files.append(css_path)

    print(f"\n[OK] Compressing dictionary: {zip_filename}")
    with zipfile.ZipFile(os.path.join(output_dir, zip_filename), 'w', zipfile.ZIP_DEFLATED) as zipf:
        for path in generated_files:
            if os.path.exists(path):
                zipf.write(path, os.path.basename(path))
    zip_path = os.path.join(output_dir, zip_filename)
    if validate:
        validate_yomitan_zip(zip_path, mode, allow_open=open_panels)
    if not keep_json:
        for f in [path for path in generated_files if os.path.basename(path).startswith("term_bank_")]:
            remove_generated_file(f, warn=True)

    print("\n=== Parser Stats ===")
    print(f"[*] Parsed HTML Entry Buffers: {parsed_html_entries}")
    print(f"[*] Skipped HTML Entry Buffers: {skipped_html_entries}")
    print(f"[*] Redirect Aliases: {redirect_aliases}")
    print(f"[*] Parsed VIP Panels: {extractor.stats['vip_parsed']}")
    print(f"[*] Fallback Panels: {extractor.stats['fallback']}")
    print(f"[*] Errors: {extractor.stats['errors']}")
    print(f"[OK] Done! Dictionary package generated with V{VERSION}.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="OALD 10 to Yomitan Dictionary Builder")
    parser.add_argument('-i', '--input', required=True, help="Input file path (e.g., oaldpe.txt)")
    parser.add_argument('-o', '--output', default="./yomitan_v3", help="Output folder path")
    parser.add_argument('-m', '--mode', choices=['bilingual', 'mono'], default='bilingual',
                        help="Dictionary content mode: 'bilingual' (EN-ZH) or 'mono' (EN-EN)")
    parser.add_argument('-u', '--ui-lang', choices=['zh', 'en'], default='zh',
                        help="Language for UI elements like tags and descriptions")
    parser.add_argument('--debug', action='store_true',
                        help="Build only the default debug words and write readable JSON. Panels open by default in debug.")
    parser.add_argument('--test-words', default=None,
                        help="Comma-separated words for debug builds. Passing this flag implies --debug.")
    parser.add_argument('--open-panels', action='store_true',
                        help="Force details panels to be open in the generated structured content.")
    parser.add_argument('--closed-panels', action='store_true',
                        help="Keep details panels closed even in debug builds.")
    parser.add_argument('--keep-json', action='store_true',
                        help="Keep term_bank JSON files after creating the zip. Debug builds keep them by default.")
    parser.add_argument('--discard-json', action='store_true',
                        help="Remove term_bank JSON files after creating the zip, even in debug builds.")
    parser.add_argument('--skip-validation', action='store_true',
                        help="Skip the generated zip validation step.")
    args = parser.parse_args()

    if args.open_panels and args.closed_panels:
        parser.error("--open-panels and --closed-panels cannot be used together")
    if args.keep_json and args.discard_json:
        parser.error("--keep-json and --discard-json cannot be used together")

    debug_mode = args.debug or args.test_words is not None
    test_words = DEFAULT_TEST_WORDS
    if args.test_words is not None:
        test_words = [w.strip() for w in re.split(r'[,;]', args.test_words) if w.strip()]
        if not test_words:
            parser.error("--test-words must contain at least one word")

    open_panels = args.open_panels or (debug_mode and not args.closed_panels)
    keep_json = args.keep_json or (debug_mode and not args.discard_json)

    package_dictionary(
        args.input,
        args.output,
        args.mode,
        args.ui_lang,
        keep_json=keep_json,
        open_panels=open_panels,
        debug_mode=debug_mode,
        test_words=test_words,
        validate=not args.skip_validation,
    )
