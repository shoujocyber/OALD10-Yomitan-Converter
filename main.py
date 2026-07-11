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
from datetime import date
from bs4 import BeautifulSoup
from tqdm import tqdm

VERSION = "3.1.0"
AUTHOR = "shoujocyber"
PROJECT_URL = "https://github.com/shoujocyber/OALD10-Yomitan-Converter"
SOURCE_FORUM_URL = "https://forum.freemdict.com/t/topic/43710"
FREEMDICT_RELEASE_URL = "https://forum.freemdict.com/t/topic/44052"

# ==========================================
# 🌍 i18n Dictionary for UI & Metadata
# ==========================================
I18N_TEXT = {
    "zh": {
        "desc_bilingual": "牛津高阶英汉双解词典(第10版) 纯净优化版",
        "desc_mono": "牛津高阶词典(第10版) 中文标签辅助英英版",
        "attribution": f"Oxford Advanced Learner's Dictionary, 10th Edition (Oxford University Press)；OALDPEX 数据由 xingxingla 分享：{SOURCE_FORUM_URL}",
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
        "attribution": f"Oxford Advanced Learner's Dictionary, 10th Edition (Oxford University Press); OALDPEX data shared by xingxingla: {SOURCE_FORUM_URL}",
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
RICH_BOLD_OPEN = "\ue000"
RICH_BOLD_CLOSE = "\ue001"
RICH_GLOSS_OPEN = "\ue002"
RICH_GLOSS_CLOSE = "\ue003"
RICH_MARKERS = (RICH_BOLD_OPEN, RICH_BOLD_CLOSE, RICH_GLOSS_OPEN, RICH_GLOSS_CLOSE)

# Immersion keeps short Chinese scaffolding while definitions, examples, notes,
# and panel bodies remain English-only. Global mode keeps none of these labels.
IMMERSION_METADATA_CLASSES = frozenset({
    "shcut",
    "grammar",
    "labels",
    "dis-g",
    "use",
    "subj",
    "belong-to",
    "variants",
    "v-g",
    "inflections",
    "inflected_form",
})
IMMERSION_ALLOWED_ZH_CLASSES = frozenset({
    "oald-shortcut",
    "oald-tag-grammar",
    "oald-tag-grammar-long",
    "oald-tag-topic",
    "oald-variant",
    "oald-variant-inline",
    "oald-label",
    "oald-panel-title",
})
CJK_TEXT_RE = re.compile(r'[\u3400-\u4dbf\u4e00-\u9fff]')
GRAMMAR_LABEL_ZH = {
    "countable": "可数",
    "uncountable": "不可数",
    "singular": "单数",
    "plural": "复数",
    "transitive": "及物",
    "intransitive": "不及物",
    "only before noun": "仅用于名词前",
    "usually before noun": "通常用于名词前",
    "not before noun": "不用于名词前",
    "not usually before noun": "通常不用于名词前",
    "after noun": "用于名词后",
    "usually singular": "通常用单数",
    "usually plural": "通常用复数",
    "often passive": "常用于被动语态",
    "usually passive": "通常用于被动语态",
    "no passive": "不用于被动语态",
    "singular or plural verb": "谓语动词可用单数或复数",
}

POS_TAG_MAP = {
    "noun": "noun",
    "verb": "verb",
    "adjective": "adj",
    "adverb": "adv",
    "pronoun": "pron",
    "preposition": "prep",
    "conjunction": "conj",
    "exclamation": "excl",
    "determiner": "det",
    "definite article": "def-article",
    "indefinite article": "indef-article",
    "number": "num",
    "ordinal number": "ordinal-num",
    "modal verb": "modal",
    "auxiliary verb": "aux",
    "linking verb": "linking-v",
    "phrasal verb": "phrasal-v",
    "prefix": "prefix",
    "suffix": "suffix",
    "combining form": "combining-form",
    "infinitive marker": "inf-marker",
    "short form": "short-form",
    "abbreviation": "abbr",
    "idiom": "idiom",
    "symbol": "symb",
    "n.": "noun",
    "adj.": "adj",
}

POS_RULE_MAP = {
    "noun": "n",
    "verb": "v",
    "adjective": "adj",
    "adverb": "adv",
    "pronoun": "pron",
    "preposition": "prep",
    "conjunction": "conj",
    "phrasal verb": "v_phr",
    "n.": "n",
    "adj.": "adj",
}

INTEGRITY_COUNT_KEYS = (
    "entries",
    "senses",
    "definitions",
    "translations",
    "examples",
    "topics",
    "sense_core_labels",
    "usage_notes",
    "panels",
    "panel_payloads",
    "xref_groups",
    "xref_links",
)


def normalize_label(label):
    text = re.sub(r'\s+', ' ', str(label or '')).strip()
    return LABEL_DECORATION_RE.sub('', text).strip()


def localize_grammar_label(label):
    """Translate only the closed set of structural grammar descriptors."""
    parts = re.split(r'(,\s*|\s+\+\s+)', normalize_label(label).casefold())
    localized = []
    for part in parts:
        if not part:
            continue
        if re.fullmatch(r',\s*', part):
            localized.append('，')
        elif re.fullmatch(r'\s+\+\s+', part):
            localized.append('；')
        elif part in GRAMMAR_LABEL_ZH:
            localized.append(GRAMMAR_LABEL_ZH[part])
        else:
            return ""
    return "".join(localized)


def split_pos_values(raw_pos):
    return [part.strip().lower() for part in str(raw_pos or "").split(",") if part.strip()]


def map_pos_metadata(raw_pos):
    tag_names = []
    rule_names = []
    for part in split_pos_values(raw_pos):
        tag_name = POS_TAG_MAP.get(part)
        if not tag_name:
            tag_name = re.sub(r"[^a-z0-9]+", "-", part).strip("-")
        if tag_name and tag_name not in tag_names:
            tag_names.append(tag_name)

        rule_name = POS_RULE_MAP.get(part)
        if rule_name and rule_name not in rule_names:
            rule_names.append(rule_name)
    return tag_names, " ".join(rule_names)


def has_visible_value(value):
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, dict):
        return any(has_visible_value(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(has_visible_value(item) for item in value)
    return bool(value)


INTERNAL_REFERENCE_PREFIX = "oalecd_ref_"
SENSE_HEADER_FIELDS = (
    "shortcut", "idiom", "phrasal_verb", "pattern", "variants", "grammar", "core_labels"
)
SENSE_NUMBERED_FIELDS = ("eng", "definition_links", "chn", "examples", "notes", "see_also")


def is_internal_reference_key(word):
    return str(word or "").casefold().startswith(INTERNAL_REFERENCE_PREFIX)


def sense_has_numbered_content(sense):
    return any(has_visible_value(sense.get(field)) for field in SENSE_NUMBERED_FIELDS)


def sense_has_body_content(sense):
    if sense_has_numbered_content(sense):
        return True
    return any(has_visible_value(panel.get("data")) for panel in sense.get("panels", []))


def sense_has_visible_content(sense):
    return (
        any(has_visible_value(sense.get(field)) for field in SENSE_HEADER_FIELDS)
        or sense_has_body_content(sense)
    )


def entry_has_visible_content(entry_ir):
    if any(has_visible_value(value) for value in entry_ir.get("phonetics", {}).values()):
        return True
    if any(
        has_visible_value(entry_ir.get(field))
        for field in ("variants", "notes", "global_see_also", "phrasal_verbs_links")
    ):
        return True
    if any(sense_has_visible_content(sense) for sense in entry_ir.get("senses", [])):
        return True
    return any(has_visible_value(panel.get("data")) for panel in entry_ir.get("panels", []))


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
        "language bank at": "Language bank 语言库",
        "synonyms at": "Synonyms 辨析",
        "homophones at": "Homophones 同音词",
        "wordfinder note at": "Wordfinder 词汇扩展",
        "collocations at": "Collocations 搭配",
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
        "language bank at": "Language bank",
        "synonyms at": "Synonyms",
        "homophones at": "Homophones",
        "wordfinder note at": "Wordfinder",
        "collocations at": "Collocations",
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
:root {{ --oald-tag-font: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, "Microsoft YaHei", sans-serif; --oald-shortcut-fg: #8A4F1F; --oald-grammar-fg: #0B5C91; --oald-topic-fg: #5B6420; --oald-variant-fg: #666666; }}
@media (prefers-color-scheme: dark) {{ :root {{ --oald-shortcut-fg: #D4A06A; --oald-grammar-fg: #8BC7F5; --oald-topic-fg: #C2C86A; --oald-variant-fg: #B8B8B8; }} }}
.nightMode, .night-mode, [data-theme="dark"] {{ --oald-shortcut-fg: #D4A06A; --oald-grammar-fg: #8BC7F5; --oald-topic-fg: #C2C86A; --oald-variant-fg: #B8B8B8; }}

/* Sense layout with a hanging number column. */
div[data-sc-class="oald-sense"] {{ padding-left: 1.72em; margin-bottom: 10px; line-height: 1.52; }}
div[data-sc-class="oald-sense-single"] {{ margin-bottom: 10px; line-height: 1.52; }}
div[data-sc-class="oald-entry-tail"] {{ margin-top: -4px; }}

div[data-sc-class="oald-sense-header"], div[data-sc-class="oald-sense-header-numbered"] {{ margin-bottom: 3px; }}
div[data-sc-class="oald-sense-header"] {{ display: block; }}
div[data-sc-class="oald-sense-header-numbered"] {{ margin-left: -1.72em; padding-left: 1.72em; position: relative; display: block; min-width: 0; }}

span[data-sc-class="oald-def-num"] {{ position: absolute; left: 0; width: 1.25em; display: inline-block; text-align: center; font-weight: 800; font-size: 1.05em; color: var(--text-color); }}
span[data-sc-class="oald-head-main"] {{ display: inline; min-width: 0; }}
span[data-sc-class="oald-shortcut"] {{ display: inline-block; vertical-align: baseline; max-width: 100%; box-sizing: border-box; font-size: 0.84em; font-weight: 600; line-height: 1.36; font-family: var(--oald-tag-font); color: #8A4F1F; color: var(--oald-shortcut-fg); color: color-mix(in srgb, var(--text-color) 76%, #B56A2A 24%); background-color: rgba(181, 106, 42, 0.12); border: 1px solid rgba(181, 106, 42, 0.26); border-left: 2px solid rgba(181, 106, 42, 0.62); border-radius: 4px; padding: 0 5px; margin-right: 0.35em; white-space: normal; overflow-wrap: break-word; }}
span[data-sc-class="oald-idiom-title"] {{ font-weight: 700; color: #B63F5A; margin-right: 0.45em; }}

/* Compact semantic labels. */
span[data-sc-class="oald-tag-grammar"] {{ display: inline-block; vertical-align: baseline; box-sizing: border-box; background-color: rgba(0, 120, 215, 0.08); color: #0B5C91; color: var(--oald-grammar-fg); color: color-mix(in srgb, var(--text-color) 72%, #0078D7 28%); border: 1px solid rgba(0, 120, 215, 0.30); border-left: 2px solid rgba(0, 120, 215, 0.62); border-radius: 4px; padding: 0 5px; font-size: 0.84em; line-height: 1.36; font-weight: 600; font-family: var(--oald-tag-font); white-space: nowrap; margin-right: 0.35em; }}
span[data-sc-class="oald-tag-grammar-long"] {{ display: inline-block; vertical-align: baseline; max-width: 100%; box-sizing: border-box; background-color: rgba(0, 120, 215, 0.08); color: #0B5C91; color: var(--oald-grammar-fg); color: color-mix(in srgb, var(--text-color) 72%, #0078D7 28%); border: 1px solid rgba(0, 120, 215, 0.30); border-left: 2px solid rgba(0, 120, 215, 0.62); border-radius: 4px; padding: 0 5px; font-size: 0.84em; line-height: 1.36; font-weight: 600; font-family: var(--oald-tag-font); white-space: normal; overflow-wrap: break-word; margin-right: 0.35em; }}
span[data-sc-class="oald-tag-topic"] {{ display: inline-block; vertical-align: baseline; max-width: 100%; box-sizing: border-box; background-color: rgba(112, 122, 36, 0.10); color: #5B6420; color: var(--oald-topic-fg); color: color-mix(in srgb, var(--text-color) 70%, #707A24 30%); border: 1px solid rgba(112, 122, 36, 0.32); border-left: 2px solid rgba(112, 122, 36, 0.66); border-radius: 4px; padding: 0 5px; font-size: 0.84em; line-height: 1.36; font-weight: 600; font-family: var(--oald-tag-font); white-space: normal; overflow-wrap: break-word; margin-right: 0.35em; }}
span[data-sc-class="oald-variant-inline"] {{ display: inline-block; vertical-align: baseline; max-width: 100%; box-sizing: border-box; font-size: 0.91em; font-style: normal; font-weight: 500; line-height: 1.36; font-family: var(--oald-tag-font); color: #666666; color: var(--oald-variant-fg); color: color-mix(in srgb, var(--text-color) 82%, #777 18%); opacity: 0.90; background-color: rgba(128, 128, 128, 0.10); border: 1px solid rgba(128, 128, 128, 0.22); border-radius: 3px; padding: 0 0.32em; margin-right: 0.45em; white-space: normal; overflow-wrap: break-word; }}

/* Construction patterns such as [+ speech]. */
span[data-sc-class="oald-pattern"] {{ font-weight: 700; color: #007F7A; white-space: nowrap; font-size: 0.94em; margin-right: 0.35em; display: inline-block; }}

/* Definitions, usage notes and examples. */
div[data-sc-class="oald-eng"] {{ margin-top: 2px; margin-bottom: {def_margin_bottom}; line-height: 1.5; font-size: {def_font_size}; font-weight: {def_font_weight}; color: var(--text-color); opacity: 0.98; }}
div[data-sc-class="oald-chn"] {{ font-size: 1.01em; font-weight: 700; margin-bottom: 5px; line-height: 1.46; color: var(--text-color); }}
div[data-sc-class="oald-note"] {{ margin: 4px 0 5px; padding: 2px 0 2px 0.65em; border-left: 2px solid rgba(66, 133, 244, 0.48); font-size: 0.94em; line-height: 1.46; color: var(--text-color); opacity: 0.92; }}
div[data-sc-class="oald-note-zh"] {{ margin-top: 1px; }}
div[data-sc-class="oald-ex-en"], div[data-sc-class="oald-panel-ex-en"] {{ padding-left: {ex_indent}; text-indent: -{ex_indent}; margin-bottom: 1px; line-height: 1.42; font-size: {ex_font_size}; color: var(--text-color); opacity: {ex_opacity}; }}
div[data-sc-class="oald-ex-zh"], div[data-sc-class="oald-panel-ex-zh"] {{ padding-left: {ex_indent}; text-indent: -{ex_indent}; margin-bottom: 4px; line-height: 1.42; }}
span[data-sc-class="oald-sym"] {{ opacity: 0.58; font-family: Arial, sans-serif; display: inline-block; width: {ex_indent}; text-indent: 0; }}
span[data-sc-class="oald-ex-pattern"] {{ color: #007F7A; font-weight: 700; margin-right: 0; }}

/* Cross-reference links, such as See also and Phrasal verbs. */
div[data-sc-class="oald-link"] {{ margin-top: 2px; margin-bottom: 4px; font-size: 0.95em; display: block; line-height: 1.6; word-break: break-word; }}
div[data-sc-class="oald-link"] a {{ white-space: nowrap; }}
span[data-sc-class="oald-cross-ref-icon"] {{ font-weight: 700; color: #0078D7 !important; font-size: 1.05em; font-family: Arial, sans-serif; }}
span[data-sc-class="oald-label"] {{ font-weight: 700; color: var(--text-color); opacity: 0.84; font-style: normal; }}

/* Compact details panels with an in-flow disclosure marker. */
details[data-sc-class="oald-panel"] {{ margin: 2px 0; padding: 0; }}
summary[data-sc-class="oald-panel-title"] {{ list-style: none; position: relative; display: block; font-weight: 700; cursor: pointer; color: var(--text-color); line-height: 1.32; padding: 1px 0 1px 0.95em; margin: 0; }}
summary[data-sc-class="oald-panel-title"]::-webkit-details-marker {{ display: none; }}
summary[data-sc-class="oald-panel-title"]::marker {{ content: ""; }}
summary[data-sc-class="oald-panel-title"]::before {{ content: ""; position: absolute; left: 0.08em; top: 50%; width: 0; height: 0; border-top: 0.30em solid transparent; border-bottom: 0.30em solid transparent; border-left: 0.44em solid currentColor; opacity: 0.86; transform: translateY(-50%); transform-origin: 38% 50%; }}
details[data-sc-class="oald-panel"][open] > summary[data-sc-class="oald-panel-title"]::before {{ transform: translateY(-50%) rotate(90deg); }}
div[data-sc-class="oald-panel-content"] {{ background-color: rgba(128, 128, 128, 0.05); border-left: 3px solid #4285f4; border-radius: 0 4px 4px 0; padding: 6px 8px; margin-top: 4px; }}
div[data-sc-class="oald-group"] {{ font-weight: 700; color: #0078D7; margin-top: 4px; margin-bottom: 2px; font-size: 0.95em; }}
div[data-sc-class="oald-panel-indent"] {{ padding-left: 1.2em; margin-top: 2px; margin-bottom: 2px; }}

/* Entry-level metadata. */
div[data-sc-class="oald-phonetics"] {{ margin-bottom: 4px; opacity: 0.9; margin-top: 4px; }}
div[data-sc-class="oald-variant"] {{ opacity: 0.8; font-style: italic; margin-bottom: 4px; }}
"""

# ==========================================
# Module 1: Data Extractor
# ==========================================
class OaldExtractor:
    def __init__(self, mode="bilingual", ui_lang="zh"):
        self.mode = mode
        self.ui_lang = ui_lang
        self.i18n = I18N_TEXT[ui_lang]
        self.stats = {
            "vip_parsed": {},
            "fallback": {},
            "errors": {},
            "empty_panel_data": {},
            "empty_sense_placeholders": 0,
            "source": {key: 0 for key in INTEGRITY_COUNT_KEYS},
            "parsed": {key: 0 for key in INTEGRITY_COUNT_KEYS},
            "samples": {
                "definition_mismatch": [],
                "example_mismatch": [],
                "topic_mismatch": [],
                "core_label_mismatch": [],
                "empty_panel_data": [],
                "empty_sense_placeholders": [],
            },
        }

    def clean_text(self, text):
        if not text: return ""
        text = re.sub(r'\s+', ' ', text).strip()
        return text.replace("( ", "(").replace(" )", ")")

    def _keep_mono_translation_node(self, node):
        # Panel titles are parsed separately and localized by ui_lang.
        if node.find_parent('unboxx'):
            return True
        if self.ui_lang != "zh":
            return False

        # Chinese in definitions, examples, long notes, and panel bodies is
        # dictionary content rather than compact learning scaffolding.
        if node.find_parent('span', class_='unbox'):
            return False
        if node.find_parent('ul', class_='examples'):
            return False
        if node.find_parent(['span', 'div'], class_=['def', 'un', 'x', 'unx']):
            return False

        parent = node.parent
        while parent is not None:
            if IMMERSION_METADATA_CLASSES.intersection(parent.get('class') or []):
                return True
            parent = parent.parent
        return False

    def _rich_style(self, tag):
        classes = set(tag.get('class') or [])
        if 'gloss' in classes:
            return 'gloss'
        if tag.name in {'strong', 'b'} or classes.intersection({'eb', 'ei', 'Ref', 'cl', 'xh_bold', 'xh', 'ndv'}):
            return 'bold'
        return None

    def _mark_rich_text(self, node):
        if not node:
            return

        candidates = []
        for tag in node.find_all(['span', 'a', 'strong', 'b']):
            style = self._rich_style(tag)
            if style:
                candidates.append((tag, style))

        candidate_styles = {id(tag): style for tag, style in candidates}
        filtered = []
        for tag, style in candidates:
            parent = tag.parent
            redundant = False
            while parent is not None and parent is not node:
                if candidate_styles.get(id(parent)) == style:
                    redundant = True
                    break
                parent = parent.parent
            if not redundant:
                filtered.append((tag, style))

        # Replace deepest nodes first so different styles can nest without losing content.
        filtered.sort(key=lambda item: sum(1 for _ in item[0].parents), reverse=True)
        markers = {
            'bold': (RICH_BOLD_OPEN, RICH_BOLD_CLOSE),
            'gloss': (RICH_GLOSS_OPEN, RICH_GLOSS_CLOSE),
        }
        for tag, style in filtered:
            if tag.parent is None:
                continue
            open_marker, close_marker = markers[style]
            tag.replace_with(f"{open_marker}{tag.get_text()}{close_marker}")

    def _parse_usage_note(self, note):
        zh_node = note.find(['unx', 'undt', 'unxt', 'chn'])
        zh_text = self.clean_text(zh_node.get_text()) if zh_node else ""
        if zh_node:
            zh_node.decompose()
        self._mark_rich_text(note)
        return {
            "kind": note.get('un') or "note",
            "en": self.clean_text(note.get_text()),
            "zh": zh_text,
        }

    def _extract_topic_tags(self, topic):
        names = topic.find_all('span', class_='topic_name')
        levels = topic.find_all('span', class_='topic_cefr')
        tags = []

        if names:
            for index, name_node in enumerate(names):
                name = self.clean_text(name_node.get_text())
                if not name:
                    continue
                level = ""
                if index < len(levels):
                    level = self.clean_text(levels[index].get_text()).upper()
                label = f"Topic: {name}"
                if level:
                    label += f" ({level})"
                tags.append({"en": label, "zh": ""})
        else:
            for level_node in levels:
                level = self.clean_text(level_node.get_text()).upper()
                if level:
                    tags.append({"en": f"CEFR: {level}", "zh": ""})

        return tags

    def _sense_core_labels(self, sense):
        group = sense.find_parent('span', class_='idm-g')
        if group is None:
            group = sense.find_parent('span', class_='pv-g')
        if group is None:
            return []

        group_senses = group.find_all('li', class_='sense')
        if not group_senses or group_senses[0] is not sense:
            return []

        labels = []
        for symbols in group.find_all('div', class_='symbols'):
            owner = symbols.find_parent('span', class_=['idm-g', 'pv-g'])
            if owner is not group:
                continue
            for span in symbols.find_all('span'):
                for cls in span.get('class', []):
                    match = re.fullmatch(r'ox([35])ksymsub_(.+)', cls)
                    if not match:
                        continue
                    vocabulary = "Oxford3000" if match.group(1) == "3" else "Oxford5000"
                    for label in (vocabulary, match.group(2).upper()):
                        if label not in labels:
                            labels.append(label)
        return labels

    def _record_source_entry(self, entry_block):
        source = self.stats["source"]
        source["entries"] += 1

        senses = entry_block.find_all('li', class_='sense')
        source["senses"] += len(senses)
        sense_snapshots = []
        for sense in senses:
            def_tag = sense.find('span', class_='def')
            deft_tag = sense.find('deft')
            has_definition = bool(def_tag and self.clean_text(def_tag.get_text()))
            has_translation = bool(deft_tag and self.clean_text(deft_tag.get_text()))
            source["definitions"] += has_definition
            source["translations"] += has_translation

            example_count = 0
            example_list_count = 0
            for ex_ul in sense.find_all('ul', class_='examples'):
                if ex_ul.find_parent('span', class_='unbox'):
                    continue
                example_list_count += 1
                example_count += sum(
                    1 for ex_li in ex_ul.find_all('li')
                    if ex_li.find('span', class_=['x', 'unx'])
                )
            retained_examples = min(example_count, 5)
            source["examples"] += retained_examples

            source_topics = []
            for topic in sense.find_all('span', class_='topic-g'):
                for topic_tag in self._extract_topic_tags(topic):
                    if topic_tag not in source_topics:
                        source_topics.append(topic_tag)
            source["topics"] += len(source_topics)
            source_core_labels = self._sense_core_labels(sense)
            source["sense_core_labels"] += len(source_core_labels)

            sense_snapshots.append({
                "id": sense.get("id") or "<no id>",
                "definition": has_definition,
                "examples": retained_examples,
                "example_lists": example_list_count,
                "topics": len(source_topics),
                "core_labels": len(source_core_labels),
            })

        source["usage_notes"] += len(entry_block.find_all('span', class_='un'))
        panel_nodes = entry_block.find_all('span', class_='unbox', unbox=True)
        source["panels"] += len(panel_nodes)
        for panel in panel_nodes:
            payload_parts = [
                str(text_node).strip()
                for text_node in panel.find_all(string=True)
                if str(text_node).strip()
                and not text_node.find_parent('span', class_='box_title')
            ]
            source["panel_payloads"] += bool(payload_parts)

        xrefs = [
            xref for xref in entry_block.find_all('span', class_='xrefs')
            if not xref.find_parent('span', class_=['unbox', 'un', 'def']) and xref.find('a', class_='Ref')
        ]
        source["xref_groups"] += len(xrefs)
        source["xref_links"] += sum(len(xref.find_all('a', class_='Ref')) for xref in xrefs)
        return sense_snapshots

    def _record_parsed_entry(self, entry_ir, source_senses):
        parsed = self.stats["parsed"]
        parsed["entries"] += 1
        parsed["senses"] += len(entry_ir["senses"])
        parsed["usage_notes"] += len(entry_ir.get("notes", []))

        all_panels = list(entry_ir.get("panels", []))
        xref_groups = list(entry_ir.get("global_see_also", []))
        for sense_index, sense in enumerate(entry_ir["senses"]):
            parsed["definitions"] += bool(sense.get("eng"))
            parsed["translations"] += bool(sense.get("chn"))
            parsed["examples"] += len(sense.get("examples", []))
            parsed["topics"] += sum(
                1 for grammar in sense.get("grammar", [])
                if grammar.get("en", "").startswith(("Topic:", "CEFR:"))
            )
            parsed["sense_core_labels"] += len(sense.get("core_labels", []))
            parsed["usage_notes"] += len(sense.get("notes", []))
            all_panels.extend(sense.get("panels", []))
            xref_groups.extend(sense.get("see_also", []))
            if not sense_has_visible_content(sense):
                self.stats["empty_sense_placeholders"] += 1
                samples = self.stats["samples"]["empty_sense_placeholders"]
                if len(samples) < 12:
                    source_id = (
                        source_senses[sense_index]["id"]
                        if sense_index < len(source_senses)
                        else "<unknown>"
                    )
                    samples.append({"word": entry_ir["word"], "sense": source_id})

        parsed["panels"] += len(all_panels)
        parsed["panel_payloads"] += sum(
            has_visible_value(panel.get("data")) for panel in all_panels
        )
        for panel in all_panels:
            if not has_visible_value(panel.get("data")):
                panel_type = panel.get("type") or "<missing>"
                empty_counts = self.stats["empty_panel_data"]
                empty_counts[panel_type] = empty_counts.get(panel_type, 0) + 1
                samples = self.stats["samples"]["empty_panel_data"]
                if len(samples) < 20:
                    samples.append({
                        "word": entry_ir["word"],
                        "type": panel_type,
                        "title": panel.get("title_en", ""),
                    })
            if panel.get("type") == "synonyms" and isinstance(panel.get("data"), dict):
                parsed["usage_notes"] += len(panel["data"].get("notes", []))

        parsed["xref_groups"] += len(xref_groups)
        parsed["xref_links"] += sum(len(group.get("links", [])) for group in xref_groups)

        for source_sense, parsed_sense in zip(source_senses, entry_ir["senses"]):
            if source_sense["definition"] != bool(parsed_sense.get("eng")):
                samples = self.stats["samples"]["definition_mismatch"]
                if len(samples) < 12:
                    samples.append({
                        "word": entry_ir["word"],
                        "sense": source_sense["id"],
                        "source": source_sense["definition"],
                        "parsed": bool(parsed_sense.get("eng")),
                    })
            if source_sense["examples"] != len(parsed_sense.get("examples", [])):
                samples = self.stats["samples"]["example_mismatch"]
                if len(samples) < 12:
                    samples.append({
                        "word": entry_ir["word"],
                        "sense": source_sense["id"],
                        "source": source_sense["examples"],
                        "parsed": len(parsed_sense.get("examples", [])),
                        "example_lists": source_sense["example_lists"],
                    })
            parsed_topic_count = sum(
                1 for grammar in parsed_sense.get("grammar", [])
                if grammar.get("en", "").startswith(("Topic:", "CEFR:"))
            )
            if source_sense["topics"] != parsed_topic_count:
                samples = self.stats["samples"]["topic_mismatch"]
                if len(samples) < 12:
                    samples.append({
                        "word": entry_ir["word"],
                        "sense": source_sense["id"],
                        "source": source_sense["topics"],
                        "parsed": parsed_topic_count,
                    })
            parsed_core_label_count = len(parsed_sense.get("core_labels", []))
            if source_sense["core_labels"] != parsed_core_label_count:
                samples = self.stats["samples"]["core_label_mismatch"]
                if len(samples) < 12:
                    samples.append({
                        "word": entry_ir["word"],
                        "sense": source_sense["id"],
                        "source": source_sense["core_labels"],
                        "parsed": parsed_core_label_count,
                    })

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

            elif utype == 'wordfinder':
                items = []
                seen_terms = set()
                for ref in c_root.find_all('a'):
                    term_node = ref.find('span', class_=['xh', 'xref'])
                    term = self.clean_text(term_node.get_text() if term_node else ref.get_text())
                    term_key = term.casefold()
                    if term and term_key not in seen_terms:
                        seen_terms.add(term_key)
                        items.append({"en": term, "zh": "", "examples": [], "link": term})
                if items:
                    panel_data["data"] = [{"subtitle_en": "", "subtitle_zh": "", "items": items}]

            elif utype == 'wordfamily':
                items = []
                for li in c_root.find_all('li', class_='li'):
                    word_node = li.find('span', class_='wfw')
                    if word_node:
                        word_node.replace_with(f"{RICH_BOLD_OPEN}{word_node.get_text()}{RICH_BOLD_CLOSE}")
                    item_text = self.clean_text(li.get_text())
                    if item_text:
                        items.append({"en": item_text, "zh": "", "examples": []})
                if items:
                    panel_data["data"] = [{"subtitle_en": "", "subtitle_zh": "", "items": items}]

            elif utype == 'vocab' and c_root.find('table'):
                subtitle_en = ""
                subtitle_zh = ""
                subtitle_node = c_root.find('span', class_='unbox', recursive=False)
                if subtitle_node:
                    zh_node = subtitle_node.find(['undt', 'chn'])
                    subtitle_zh = self.clean_text(zh_node.get_text()) if zh_node else ""
                    if zh_node:
                        zh_node.decompose()
                    subtitle_en = self.clean_text(subtitle_node.get_text())

                items = []
                for row in c_root.find_all('tr'):
                    cells = row.find_all('td', recursive=False)
                    if not cells:
                        continue
                    term = self.clean_text(cells[0].get_text())
                    examples = []
                    for unx in row.find_all('span', class_='unx'):
                        zh_node = unx.find(['unxt', 'undt', 'chn'])
                        zh_text = self.clean_text(zh_node.get_text()) if zh_node else ""
                        if zh_node:
                            zh_node.decompose()
                        self._mark_rich_text(unx)
                        en_text = self.clean_text(unx.get_text())
                        if en_text or zh_text:
                            examples.append({"en": en_text, "zh": zh_text})
                    if term or examples:
                        display_term = f"{RICH_BOLD_OPEN}{term}{RICH_BOLD_CLOSE}" if term else ""
                        items.append({"en": display_term, "zh": "", "examples": examples})

                for note_node in c_root.find_all('span', class_='p', recursive=False):
                    zh_node = note_node.find(['undt', 'chn'])
                    zh_text = self.clean_text(zh_node.get_text()) if zh_node else ""
                    if zh_node:
                        zh_node.decompose()
                    self._mark_rich_text(note_node)
                    en_text = self.clean_text(note_node.get_text())
                    if en_text or zh_text:
                        items.append({"en": en_text, "zh": zh_text, "examples": [], "prefix": ""})

                if items:
                    panel_data["data"] = [{
                        "subtitle_en": subtitle_en,
                        "subtitle_zh": subtitle_zh,
                        "items": items,
                    }]

            elif utype in ['langbank', 'which_word', 'british_american', 'grammar', 'more_about', 'express', 'vocab']:
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
                    elif child.name == 'span' and 'p' in (child.get('class') or []):
                        examples = []
                        for ex_ul in child.find_all('ul', class_='examples'):
                            for ex_li in ex_ul.find_all('li'):
                                ex_span = ex_li.find('span', class_=['unx', 'x', 'wx'])
                                if not ex_span:
                                    continue
                                zh_node = ex_span.find(['unxt', 'undt', 'chn'])
                                zh_text = self.clean_text(zh_node.get_text()) if zh_node else ""
                                if zh_node:
                                    zh_node.decompose()
                                self._mark_rich_text(ex_span)
                                en_text = self.clean_text(ex_span.get_text())
                                if en_text or zh_text:
                                    examples.append({"en": en_text, "zh": zh_text})
                            ex_ul.decompose()

                        zh_parts = []
                        for zh_node in list(child.find_all(['undt', 'chn'])):
                            if zh_node.find_parent(['undt', 'chn']):
                                continue
                            zh_text = self.clean_text(zh_node.get_text())
                            if zh_text:
                                zh_parts.append(zh_text)
                            zh_node.decompose()

                        self._mark_rich_text(child)
                        en_text = self.clean_text(child.get_text())
                        zh_text = self.clean_text(" ".join(zh_parts))
                        if en_text or zh_text or examples:
                            current_sec["items"].append({
                                "en": en_text,
                                "zh": zh_text,
                                "examples": examples,
                                "prefix": "",
                            })
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

                notes = []
                for note_node in c_root.find_all('span', class_='un'):
                    note_data = self._parse_usage_note(note_node)
                    if note_data["en"] or note_data["zh"]:
                        notes.append(note_data)
                    note_node.decompose()

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
                panel_data["data"] = {
                    "intro_en": intro_en,
                    "intro_zh": intro_zh,
                    "items": syn_list,
                    "notes": notes,
                }

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
                collocation_lists = c_root.find_all('ul', class_='collocs_list')
                if collocation_lists:
                    sections = []
                    for collocation_list in collocation_lists:
                        title = ""
                        heading = collocation_list.find_previous_sibling('span', class_='unbox')
                        if heading:
                            title = self.clean_text(heading.get_text())
                        elif collocation_list.parent and 'p' in (collocation_list.parent.get('class') or []):
                            title_parts = []
                            for child in collocation_list.parent.children:
                                if child is collocation_list:
                                    break
                                if getattr(child, 'get_text', None):
                                    title_parts.append(child.get_text(' ', strip=True))
                                elif str(child).strip():
                                    title_parts.append(str(child).strip())
                            title = self.clean_text(" ".join(title_parts))

                        items = [
                            self.clean_text(li.get_text())
                            for li in collocation_list.find_all('li')
                            if self.clean_text(li.get_text())
                        ]
                        if items:
                            sections.append({"title": title, "items": items})
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
                # Preserve unknown panel types as readable text and report them to validation.
                panel_data["data"] = self.clean_text(c_root.get_text())
                self.stats["fallback"][utype] = self.stats["fallback"].get(utype, 0) + 1

            if utype and utype not in self.stats["fallback"]:
                self.stats["vip_parsed"][utype] = self.stats["vip_parsed"].get(utype, 0) + 1
        except Exception:
            panel_data["data"] = self.clean_text(c_root.get_text())
            self.stats["errors"][utype] = self.stats["errors"].get(utype, 0) + 1

        return panel_data

    def parse_entry(self, html_content, word_list):
        if not word_list:
            return []

        word = word_list[0]
        aliases = [w for w in word_list if w != word]

        soup = BeautifulSoup(html_content, 'html.parser')
        entry_blocks = soup.find_all('div', class_='entry')
        if not entry_blocks: entry_blocks = soup.find_all('span', class_='idm-g')
        if not entry_blocks: return []

        results = []
        for entry_block in entry_blocks:
            source_senses = self._record_source_entry(entry_block)

            if self.mode == "mono":
                translation_nodes = entry_block.find_all(
                    ['chn', 'deft', 'uset', 'xt', 'ubx', 'unxt', 'undt']
                )
                for zh_tag in reversed(translation_nodes):
                    if self._keep_mono_translation_node(zh_tag):
                        continue
                    zh_tag.decompose()

            entry_ir = {
                "word": word, "aliases": aliases, "pos": "", "phonetics": {"uk": "", "us": ""},
                "labels": [], "senses": [], "panels": [], "variants": [], "notes": [],
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
                        if cls.startswith('ox3ksym_'):
                            entry_ir["labels"].extend(["Oxford3000", cls.split('_')[-1].upper()])
                        elif cls.startswith('ox5ksym_'):
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
                    if v_txt:
                        entry_ir["variants"].append({"en": v_txt, "zh": chn_txt})
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

            for wo in entry_block.find_all('span', class_='unbox', unbox='wordorigin'):
                panel_data = self._parse_panel(wo)
                entry_ir["panels"].append(panel_data)
                wo.decompose()

            for note_node in entry_block.find_all('span', class_='un'):
                if note_node.find_parent('li', class_='sense') or note_node.find_parent('span', class_='unbox'):
                    continue
                note_data = self._parse_usage_note(note_node)
                if note_data["en"] or note_data["zh"]:
                    entry_ir["notes"].append(note_data)
                note_node.decompose()

            for sense in entry_block.find_all('li', class_='sense'):
                sense_data = {
                    "shortcut": {}, "idiom": "", "phrasal_verb": "", "pattern": "",
                    "variants": [], "core_labels": self._sense_core_labels(sense),
                    "grammar": global_grammar.copy(),
                    "eng": "", "definition_links": [], "chn": "", "examples": [], "notes": [],
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
                    if variant.find_parent('span', class_='def'):
                        continue
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
                    for topic_tag in self._extract_topic_tags(topic):
                        if topic_tag not in sense_data["grammar"]:
                            sense_data["grammar"].append(topic_tag)
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

                for note_node in sense.find_all('span', class_='un'):
                    if note_node.find_parent('span', class_='unbox'):
                        continue
                    note_data = self._parse_usage_note(note_node)
                    if note_data["en"] or note_data["zh"]:
                        sense_data["notes"].append(note_data)
                    note_node.decompose()

                for xref in sense.find_all('span', class_='xrefs'):
                    if xref.find_parent('span', class_='unbox'): continue
                    refs = []
                    for ref in xref.find_all('a', class_='Ref'):
                        xh = ref.find('span', class_='xh')
                        if xh: refs.append(xh.get_text(strip=True))
                        else: refs.append(ref.get_text(strip=True))

                    definition_parent = xref.find_parent('span', class_='def')
                    if definition_parent:
                        if refs:
                            sense_data["definition_links"] = refs
                            xref.replace_with(" | ".join(refs))
                        continue

                    prefix_node = xref.find('span', class_='prefix')
                    prefix_txt = prefix_node.get_text(strip=True) if prefix_node else "See also"
                    prefix_txt = prefix_txt[0].upper() + prefix_txt[1:] if prefix_txt else "See also:"
                    if not prefix_txt.endswith(':'): prefix_txt += ':'
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
                for ex_ul in sense.find_all('ul', class_='examples'):
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
                if xref.find_parent('span', class_=['unbox', 'def']): continue
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

            self._record_parsed_entry(entry_ir, source_senses)
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

    def render_definition(self, sense):
        definition = sense.get("eng", "")
        links = [link for link in sense.get("definition_links", []) if link]
        linked_text = " | ".join(links)
        if links and self._text_key(definition) == self._text_key(linked_text):
            content = []
            for index, link in enumerate(links):
                content.append({"tag": "a", "href": f"?query={link}&wildcards=off", "content": link})
                if index < len(links) - 1:
                    content.append(" | ")
            return content
        return self.render_rich_text(definition)

    @staticmethod
    def _text_key(text):
        return re.sub(r'\s+', ' ', str(text or '')).strip().casefold()

    def render_rich_text(self, text, prefix=""):
        text = str(text or "")
        if not any(marker in text for marker in RICH_MARKERS):
            return prefix + text if prefix or text else ""

        open_markers = {
            RICH_BOLD_OPEN: 'bold',
            RICH_GLOSS_OPEN: 'gloss',
        }
        close_markers = {
            RICH_BOLD_CLOSE: 'bold',
            RICH_GLOSS_CLOSE: 'gloss',
        }
        root = []
        stack = [(None, root)]
        buffer = []

        def flush_buffer():
            if not buffer:
                return
            value = "".join(buffer)
            buffer.clear()
            target = stack[-1][1]
            if target and isinstance(target[-1], str):
                target[-1] += value
            else:
                target.append(value)

        for char in text:
            if char in open_markers:
                flush_buffer()
                node = {"style": open_markers[char], "content": []}
                stack[-1][1].append(node)
                stack.append((node["style"], node["content"]))
            elif char in close_markers and len(stack) > 1 and stack[-1][0] == close_markers[char]:
                flush_buffer()
                stack.pop()
            else:
                buffer.append(char)
        flush_buffer()

        # Returning the original marker text makes malformed nesting visible to package validation.
        if len(stack) != 1:
            return prefix + text

        style_classes = {"bold": "oald-bold", "gloss": "oald-gloss"}

        def render_parts(parts):
            rendered = []
            for part in parts:
                if isinstance(part, str):
                    if part:
                        rendered.append({"tag": "span", "content": part})
                    continue
                rendered.append({
                    "tag": "span",
                    "data": {"class": style_classes[part["style"]]},
                    "content": render_parts(part["content"]),
                })
            return rendered

        content = []
        if prefix:
            content.append({"tag": "span", "content": prefix})
        content.extend(render_parts(root))
        return content if content else ""

    def render_note(self, note):
        blocks = []
        if note.get("en"):
            blocks.append({"tag": "div", "content": self.render_rich_text(note["en"])})
        if note.get("zh"):
            blocks.append({
                "tag": "div",
                "lang": "zh",
                "data": {"class": "oald-note-zh"},
                "content": note["zh"],
            })
        if not blocks:
            return None
        return {"tag": "div", "data": {"class": "oald-note"}, "content": blocks}

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
                if item['en']:
                    item_rich = self.render_rich_text(item['en'])
                    if isinstance(item_rich, list):
                        line.extend(item_rich)
                    else:
                        line.append({"tag": "span", "content": item_rich})
                blocks.append({"tag": "div", "content": line})
                if item['zh']: blocks.append({"tag": "div", "lang": "zh", "content": item['zh']})

                ex_blocks = []
                for ex in item['examples']:
                    ex_blocks.extend(self.render_ex_pair(ex['en'], ex.get('zh'), is_panel=True))
                if ex_blocks: blocks.append({"tag": "div", "data": {"class": "oald-panel-indent"}, "content": ex_blocks})

            for note in data.get('notes', []):
                note_node = self.render_note(note)
                if note_node:
                    blocks.append(note_node)

        elif utype in ['langbank', 'which_word', 'british_american', 'wordfinder', 'wordfamily', 'grammar', 'more_about', 'express', 'vocab']:
            for sec in data:
                header = f"{sec['subtitle_en']} {sec['subtitle_zh']}".strip()
                if header: blocks.append({"tag": "div", "data": {"class": "oald-group"}, "content": header})
                for item in sec['items']:
                    if item['en']:
                        item_prefix = item.get('prefix', "■ ")
                        if item.get('link'):
                            item_content = [
                                {"tag": "span", "content": item_prefix},
                                {
                                    "tag": "a",
                                    "href": f"?query={item['link']}&wildcards=off",
                                    "content": item['en'],
                                },
                            ]
                        else:
                            item_content = self.render_rich_text(item['en'], prefix=item_prefix)
                        blocks.append({"tag": "div", "content": item_content})
                    if item['zh']: blocks.append({"tag": "div", "lang": "zh", "content": item['zh']})

                    ex_blocks = []
                    for ex in item['examples']:
                        ex_blocks.extend(self.render_ex_pair(ex['en'], ex.get('zh'), is_panel=True))
                    if ex_blocks: blocks.append({"tag": "div", "data": {"class": "oald-panel-indent"}, "content": ex_blocks})

        elif utype == 'colloc':
            for sec in data:
                header = sec['group_en']
                if sec['group_zh'] and sec['group_zh'] != sec['group_en']: header += f" ({sec['group_zh']})"
                if header: blocks.append({"tag": "div", "data": {"class": "oald-group"}, "content": header})
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
                variant_content = [{"tag": "span", "content": v["en"]}]
                if v.get("zh"):
                    variant_content.append({"tag": "span", "content": "\u00A0"})
                    variant_content.append({"tag": "span", "lang": "zh", "content": v["zh"]})
                content_blocks.append({
                    "tag": "div",
                    "data": {"class": "oald-variant"},
                    "content": variant_content,
                })

        senses = [sense for sense in entry_ir['senses'] if sense_has_visible_content(sense)]
        numbered_sense_count = sum(sense_has_numbered_content(sense) for sense in senses)
        sense_number = 0
        last_shortcut_key = ""
        for sense in senses:

            prefix = ""
            if sense_has_numbered_content(sense):
                sense_number += 1
                if numbered_sense_count > 1:
                    prefix = (
                        f"{chr(0x245F + sense_number)}"
                        if sense_number <= 20
                        else f"({sense_number})"
                    )
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
                header_content.append({"tag": "span", "data": {"class": "oald-idiom-title"}, "content": f"♦\u00A0{sense['idiom']}"})
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

            for core_label in sense.get("core_labels", []):
                header_content.append({
                    "tag": "span",
                    "data": {"class": "oald-tag-grammar"},
                    "content": core_label,
                })
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

                grammar_zh = gram['zh']
                if not grammar_zh and self.ui_lang == "zh":
                    grammar_zh = localize_grammar_label(clean_en)
                visual_length = len(clean_en) + len(grammar_zh)
                if tag_class == "oald-tag-grammar" and visual_length > 28:
                    tag_class = "oald-tag-grammar-long"

                tag_inner = [{"tag": "span", "content": clean_en}]
                if grammar_zh:
                    tag_inner.append({"tag": "span", "content": "\u00A0"})
                    tag_inner.append({"tag": "span", "lang": "zh", "content": grammar_zh})

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
                eng_rich = self.render_definition(sense)
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

            # Definition body, notes and examples.
            if sense['eng'] and not eng_in_header:
                sense_container["content"].append({"tag": "div", "data": {"class": "oald-eng"}, "content": self.render_definition(sense)})

            if sense['chn'] and not chn_in_header:
                sense_container["content"].append({"tag": "div", "lang": "zh", "data": {"class": "oald-chn"}, "content": sense['chn']})

            for ex in sense['examples']:
                sense_container["content"].extend(self.render_ex_pair(ex['en'], ex.get('zh')))

            for note in sense.get('notes', []):
                note_node = self.render_note(note)
                if note_node:
                    if pending_prefix:
                        sense_container["content"].append(self._sense_header_node(pending_prefix))
                        pending_prefix = []
                    sense_container["content"].append(note_node)

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

        # Entry-level blocks align with the sense number column on numbered entries.
        tail_blocks = []
        has_numbered_senses = numbered_sense_count > 1

        for note in entry_ir.get('notes', []):
            node = self.render_note(note)
            if node:
                tail_blocks.append(node)

        if entry_ir['global_see_also']:
            for sa in entry_ir['global_see_also']:
                node = self.render_link_block(sa.get('type'), sa.get('links', []))
                if node:
                    tail_blocks.append(node)

        if entry_ir['phrasal_verbs_links']:
            node = self.render_link_block("Phrasal verbs", entry_ir['phrasal_verbs_links'])
            if node:
                tail_blocks.append(node)

        if entry_ir['panels']:
            for p in entry_ir['panels']:
                node = self.render_unbox(p)
                if node: tail_blocks.append(node)

        if tail_blocks:
            if has_numbered_senses:
                content_blocks.append({"tag": "div", "data": {"class": "oald-entry-tail"}, "content": tail_blocks})
            else:
                content_blocks.extend(tail_blocks)

        return self._structured_definition({"tag": "div", "content": content_blocks})


# ==========================================
# Module 3: Packaging & Control Flow
# ==========================================
def infer_source_revision(input_file):
    filename = os.path.basename(str(input_file or ""))
    match = re.search(
        r'(?<!\d)(20\d{2})[._-]?([01]\d)[._-]?([0-3]\d)(?!\d)',
        filename,
    )
    if match:
        year, month, day = (int(part) for part in match.groups())
        try:
            source_date = date(year, month, day)
            return source_date.strftime("%Y.%m.%d")
        except ValueError:
            pass
    return ""


def default_dictionary_revision():
    return date.today().strftime("%Y.%m.%d")


def get_dictionary_title(mode, ui_lang, debug_mode=False):
    base_title = "OALD 10"
    if debug_mode:
        base_title += f" (Test_{int(time.time())})"

    if mode == "mono" and ui_lang == "en": return f"{base_title} (Global)"
    elif mode == "mono" and ui_lang == "zh": return f"{base_title} (Immersion)"
    elif mode == "bilingual" and ui_lang == "en": return f"{base_title} (EN Tags)"
    else: return base_title


def generate_metadata_files(
    output_dir,
    mode,
    ui_lang,
    revision,
    source_revision="",
    debug_mode=False,
):
    i18n = I18N_TEXT[ui_lang]
    base_description = i18n["desc_mono"] if mode == "mono" else i18n["desc_bilingual"]
    if ui_lang == "zh":
        description_parts = [base_description]
        if source_revision:
            description_parts.append(f"源数据 {source_revision}")
        description_parts.extend([
            f"转换器 v{VERSION}",
            f"FreeMdict 发布页：{FREEMDICT_RELEASE_URL}",
        ])
        description = "；".join(description_parts) + "。"
    else:
        description_parts = [base_description]
        if source_revision:
            description_parts.append(f"source data {source_revision}")
        description_parts.extend([
            f"converter v{VERSION}",
            f"FreeMdict release: {FREEMDICT_RELEASE_URL}",
        ])
        description = "; ".join(description_parts) + "."
    index_data = {
        "title": get_dictionary_title(mode, ui_lang, debug_mode=debug_mode),
        "format": 3,
        "revision": revision,
        "sequenced": True,
        "author": AUTHOR,
        "url": PROJECT_URL,
        "description": description,
        "attribution": i18n["attribution"],
        "sourceLanguage": "en",
        "targetLanguage": "zh" if mode == "bilingual" else "en",
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


def walk_structured_content(value, ancestor_classes=frozenset()):
    if isinstance(value, dict):
        node_class = (value.get("data") or {}).get("class")
        node_classes = ancestor_classes | ({node_class} if node_class else set())
        yield value, node_classes
        for key, item in value.items():
            if key != "data":
                yield from walk_structured_content(item, node_classes)
    elif isinstance(value, list):
        for item in value:
            yield from walk_structured_content(item, ancestor_classes)


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


def validate_yomitan_zip(
    zip_path,
    mode,
    ui_lang,
    allow_open=False,
    expected_revision=None,
    expected_source_revision=None,
):
    required_files = {"index.json", "tag_bank_1.json", "styles.css"}
    stats = {
        "term_banks": 0,
        "rows": 0,
        "structured_rows": 0,
        "redirect_rows": 0,
        "open_keys": 0,
        "style_keys": 0,
        "blank_headers": 0,
        "empty_structured_rows": 0,
        "rich_marker_leaks": 0,
        "zh_lang_nodes": 0,
        "immersion_forbidden_zh_nodes": 0,
        "global_cjk_characters": 0,
        "metadata_revision": "",
        "metadata_source_revision": "",
        "metadata_missing_fields": 0,
        "unstyled_classes": 0,
        "dangling_redirects": 0,
    }
    errors = []
    unknown_tags = set()
    structured_classes = set()
    samples = {
        "blank_headers": [],
        "empty_structured_rows": [],
        "immersion_forbidden_zh_nodes": [],
        "dangling_redirects": [],
    }
    entry_terms = set()
    redirect_targets = []

    with zipfile.ZipFile(zip_path, 'r') as zipf:
        names = set(zipf.namelist())
        missing = sorted(required_files - names)
        if missing:
            errors.append(f"missing required files: {', '.join(missing)}")

        if "index.json" in names:
            try:
                index_data = json.loads(zipf.read("index.json").decode("utf-8"))
            except Exception as exc:
                errors.append(f"index.json is not valid JSON: {exc}")
                index_data = {}

            metadata_fields = {
                "title", "format", "revision", "sequenced", "author", "url",
                "description", "attribution", "sourceLanguage", "targetLanguage",
            }
            missing_metadata = sorted(
                field for field in metadata_fields if not index_data.get(field)
            )
            stats["metadata_missing_fields"] = len(missing_metadata)
            if missing_metadata:
                errors.append(
                    f"index.json is missing metadata fields: {', '.join(missing_metadata)}"
                )

            metadata_revision = str(index_data.get("revision") or "")
            stats["metadata_revision"] = metadata_revision
            if expected_revision and metadata_revision != expected_revision:
                errors.append(
                    "index.json revision mismatch: "
                    f"expected={expected_revision}, actual={metadata_revision or '<empty>'}"
                )
            if index_data.get("format") != 3:
                errors.append("index.json format must be 3")
            if index_data.get("sequenced") is not True:
                errors.append("index.json sequenced must be true")
            if index_data.get("sourceLanguage") != "en":
                errors.append("index.json sourceLanguage must be en")
            expected_target_language = "zh" if mode == "bilingual" else "en"
            if index_data.get("targetLanguage") != expected_target_language:
                errors.append(
                    "index.json targetLanguage mismatch: "
                    f"expected={expected_target_language}, "
                    f"actual={index_data.get('targetLanguage') or '<empty>'}"
                )
            if index_data.get("url") != PROJECT_URL:
                errors.append("index.json does not contain the project URL")
            if SOURCE_FORUM_URL not in str(index_data.get("attribution") or ""):
                errors.append("index.json attribution does not contain the source forum URL")
            description = str(index_data.get("description") or "")
            if f"v{VERSION}" not in description:
                errors.append("index.json description does not contain the converter version")
            if FREEMDICT_RELEASE_URL not in description:
                errors.append("index.json description does not contain the FreeMdict release URL")
            if expected_source_revision:
                if expected_source_revision not in description:
                    errors.append(
                        "index.json description does not contain source revision "
                        f"{expected_source_revision}"
                    )
                else:
                    stats["metadata_source_revision"] = expected_source_revision

        term_banks = sorted(
            [name for name in names if re.fullmatch(r"term_bank_\d+\.json", name)],
            key=lambda name: int(re.search(r"\d+", name).group(0)),
        )
        stats["term_banks"] = len(term_banks)
        if not term_banks:
            errors.append("no term_bank_*.json files found")

        css = zipf.read("styles.css").decode("utf-8") if "styles.css" in names else ""
        defined_style_classes = set(re.findall(r'\[data-sc-class="([^"]+)"\]', css))
        expected_indent = "0.95em" if mode == "mono" else "1.35em"
        if expected_indent and f"padding-left: {expected_indent}" not in css:
            errors.append(f"styles.css does not contain expected example indent {expected_indent}")
        if "display: grid" in css or "text-indent: -1.18em" in css:
            errors.append("styles.css still contains obsolete sense-header layout rules")

        known_tags = set()
        if "tag_bank_1.json" in names:
            try:
                tag_rows = json.loads(zipf.read("tag_bank_1.json").decode("utf-8"))
                known_tags = {row[0] for row in tag_rows if isinstance(row, list) and row}
            except Exception as exc:
                errors.append(f"tag_bank_1.json is not valid JSON: {exc}")

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

                for tag_name in str(row[2] or "").split():
                    if tag_name not in known_tags and tag_name != "non-lemma":
                        unknown_tags.add(tag_name)

                definition_text = structured_text(definitions)
                stats["rich_marker_leaks"] += sum(definition_text.count(marker) for marker in RICH_MARKERS)
                if mode == "mono" and ui_lang == "en":
                    stats["global_cjk_characters"] += len(CJK_TEXT_RE.findall(definition_text))

                if isinstance(definitions, list) and definitions:
                    first_def = definitions[0]
                    if isinstance(first_def, dict) and first_def.get("type") == "structured-content":
                        stats["structured_rows"] += 1
                        entry_terms.add(str(row[0]))
                        if not definition_text.strip():
                            stats["empty_structured_rows"] += 1
                            if len(samples["empty_structured_rows"]) < 10:
                                samples["empty_structured_rows"].append(
                                    f"{bank_name}[{idx}] {row[0]}"
                                )
                    elif isinstance(first_def, list):
                        stats["redirect_rows"] += 1
                        for redirect_item in first_def:
                            if isinstance(redirect_item, list) and redirect_item:
                                redirect_targets.append((str(row[0]), str(redirect_item[0])))

                for node, node_classes in walk_structured_content(definitions):
                    if node.get("lang") == "zh":
                        stats["zh_lang_nodes"] += 1
                        if (
                            mode == "mono"
                            and ui_lang == "zh"
                            and not IMMERSION_ALLOWED_ZH_CLASSES.intersection(node_classes)
                        ):
                            stats["immersion_forbidden_zh_nodes"] += 1
                            if len(samples["immersion_forbidden_zh_nodes"]) < 10:
                                samples["immersion_forbidden_zh_nodes"].append(
                                    f"{bank_name}[{idx}] {row[0]} ({structured_text(node)[:80]})"
                                )
                    node_class = (node.get("data") or {}).get("class")
                    if node_class:
                        structured_classes.add(node_class)
                    if node_class in {"oald-sense-header", "oald-sense-header-numbered"}:
                        text = structured_text(node).strip()
                        if re.fullmatch(r"[①-⑳]|\(\d+\)", text):
                            stats["blank_headers"] += 1
                            if len(samples["blank_headers"]) < 10:
                                samples["blank_headers"].append(
                                    f"{bank_name}[{idx}] {row[0]} ({text})"
                                )

    if stats["style_keys"]:
        errors.append(f"structured content contains {stats['style_keys']} unsupported style keys")
    if stats["open_keys"] and not allow_open:
        errors.append(f"structured content contains {stats['open_keys']} open keys")
    if stats["blank_headers"]:
        errors.append(f"found {stats['blank_headers']} blank sense headers")
    if stats["empty_structured_rows"]:
        errors.append(f"found {stats['empty_structured_rows']} empty structured definition rows")
    if stats["rich_marker_leaks"]:
        errors.append(f"structured content contains {stats['rich_marker_leaks']} leaked rich-text markers")
    if mode == "mono" and ui_lang == "en" and stats["zh_lang_nodes"]:
        errors.append(f"Global edition contains {stats['zh_lang_nodes']} Chinese-language nodes")
    if mode == "mono" and ui_lang == "en" and stats["global_cjk_characters"]:
        errors.append(f"Global edition contains {stats['global_cjk_characters']} CJK text characters")
    if stats["immersion_forbidden_zh_nodes"]:
        errors.append(
            "Immersion edition contains "
            f"{stats['immersion_forbidden_zh_nodes']} Chinese body-content nodes"
        )
    if unknown_tags:
        errors.append(f"term rows contain undefined tags: {', '.join(sorted(unknown_tags))}")
    unstyled_classes = structured_classes - defined_style_classes
    stats["unstyled_classes"] = len(unstyled_classes)
    if unstyled_classes:
        errors.append(f"structured content uses undefined CSS classes: {', '.join(sorted(unstyled_classes))}")
    dangling_redirects = [
        (source, target)
        for source, target in redirect_targets
        if target not in entry_terms
    ]
    stats["dangling_redirects"] = len(dangling_redirects)
    if dangling_redirects:
        for source, target in dangling_redirects[:10]:
            samples["dangling_redirects"].append(f"{source} -> {target}")
        errors.append(f"found {len(dangling_redirects)} redirects to missing terms")

    print("\n=== Package Validation ===")
    print(f"[*] Zip: {zip_path}")
    print(f"[*] Dictionary Revision: {stats['metadata_revision'] or '<missing>'}")
    print(f"[*] Source Data Revision: {stats['metadata_source_revision'] or '<not declared>'}")
    print(f"[*] Missing Metadata Fields: {stats['metadata_missing_fields']}")
    print(f"[*] Term Banks: {stats['term_banks']}")
    print(f"[*] Rows: {stats['rows']}")
    print(f"[*] Structured Rows: {stats['structured_rows']}")
    print(f"[*] Redirect Rows: {stats['redirect_rows']}")
    print(f"[*] open/style keys: {stats['open_keys']}/{stats['style_keys']}")
    print(f"[*] Blank Sense Headers: {stats['blank_headers']}")
    print(f"[*] Empty Structured Rows: {stats['empty_structured_rows']}")
    print(f"[*] Rich Marker Leaks: {stats['rich_marker_leaks']}")
    print(f"[*] zh Language Nodes: {stats['zh_lang_nodes']}")
    print(f"[*] Immersion Body zh Nodes: {stats['immersion_forbidden_zh_nodes']}")
    print(f"[*] Global CJK Characters: {stats['global_cjk_characters']}")
    print(f"[*] Undefined Tags: {len(unknown_tags)}")
    print(f"[*] Undefined CSS Classes: {stats['unstyled_classes']}")
    print(f"[*] Dangling Redirects: {stats['dangling_redirects']}")

    if errors:
        for sample_type, sample_rows in samples.items():
            if sample_rows:
                print(f"[SAMPLES] {sample_type}: {', '.join(sample_rows)}")
        for error in errors:
            print(f"[ERROR] {error}")
        raise RuntimeError("Generated Yomitan package failed validation")

    print("[OK] Package validation passed")
    return stats


def validate_extraction_integrity(stats, mode, unexpected_parse_failures=0):
    errors = []
    print("\n=== Extraction Integrity ===")
    for key in INTEGRITY_COUNT_KEYS:
        source_count = stats["source"][key]
        parsed_count = stats["parsed"][key]
        if key == "translations" and mode == "mono":
            print(f"[*] {key}: {source_count} source / intentionally stripped")
            continue
        print(f"[*] {key}: {source_count} source / {parsed_count} parsed")
        if source_count != parsed_count:
            errors.append(f"{key} mismatch: source={source_count}, parsed={parsed_count}")

    fallback_count = sum(stats["fallback"].values())
    panel_error_count = sum(stats["errors"].values())
    print(f"[*] Fallback panels: {fallback_count}")
    print(f"[*] Panel parse errors: {panel_error_count}")
    print(f"[*] Unexpected parse failures: {unexpected_parse_failures}")
    placeholder_count = stats.get("empty_sense_placeholders", 0)
    print(f"[*] Empty source sense placeholders filtered: {placeholder_count}")
    placeholder_samples = stats.get("samples", {}).get("empty_sense_placeholders", [])
    if placeholder_samples:
        labels = [f"{sample['word']}#{sample['sense']}" for sample in placeholder_samples]
        print(f"[*] Empty placeholder samples: {', '.join(labels)}")

    if fallback_count:
        errors.append(f"found {fallback_count} panel(s) using an unknown fallback parser")
    if panel_error_count:
        errors.append(f"found {panel_error_count} panel parse error(s)")
    if unexpected_parse_failures:
        errors.append(f"found {unexpected_parse_failures} HTML record(s) with entry markup but no parsed IR")

    for sample_type in (
        "definition_mismatch", "example_mismatch", "topic_mismatch", "core_label_mismatch"
    ):
        if stats.get("samples", {}).get(sample_type):
            errors.append(f"found sense-level {sample_type.replace('_', ' ')} records")

    if errors:
        for sample_type, samples in stats.get("samples", {}).items():
            if samples:
                print(f"[SAMPLES] {sample_type}: {json.dumps(samples, ensure_ascii=False)}")
        for error in errors:
            print(f"[ERROR] {error}")
        raise RuntimeError("Source-to-IR extraction integrity check failed")

    print("[OK] Source-to-IR integrity check passed")


def package_dictionary(input_file, output_dir, mode, ui_lang, keep_json=False, open_panels=False,
                       debug_mode=False, test_words=None, validate=True, revision=None):
    os.makedirs(output_dir, exist_ok=True)
    zip_filename = get_zip_filename(mode, ui_lang, debug_mode=debug_mode)
    dictionary_revision = str(revision or "").strip() or default_dictionary_revision()
    source_revision = infer_source_revision(input_file)
    cleanup_output_dir(output_dir, zip_filename=zip_filename)
    print(f"=== OALD 10 to Yomitan V{VERSION} Engine ===")
    print(f"[*] Mode: {mode}")
    print(f"[*] UI Language: {ui_lang}")
    print(f"[*] Dictionary Revision: {dictionary_revision}")
    print(f"[*] Source Data Revision: {source_revision or '<not inferred>'}")
    print(f"[*] Debug Build: {debug_mode}")

    extractor = OaldExtractor(mode=mode, ui_lang=ui_lang)
    renderer = YomitanRenderer(mode=mode, ui_lang=ui_lang, open_panels=open_panels)
    debug_word_set = {word.casefold() for word in (test_words or DEFAULT_TEST_WORDS)}

    real_entries = {}
    redirects = {}
    parsed_html_entries = 0
    non_dictionary_html_entries = 0
    internal_reference_keys_skipped = 0
    internal_reference_samples = []
    unexpected_parse_failures = 0
    unexpected_parse_samples = []
    redirect_aliases = 0
    generated_files = []

    with open(input_file, 'r', encoding='utf-8') as f: total_lines = sum(1 for _ in f)

    def process_entry_buffer(buf):
        nonlocal parsed_html_entries, non_dictionary_html_entries
        nonlocal internal_reference_keys_skipped
        nonlocal unexpected_parse_failures, redirect_aliases
        entry_text = "\n".join(buf)
        lines = entry_text.split('\n')
        if len(lines) < 2: return
        words = [w.strip() for w in lines[0].split('|') if w.strip()]
        internal_words = [word for word in words if is_internal_reference_key(word)]
        if internal_words:
            internal_reference_keys_skipped += len(internal_words)
            for word in internal_words:
                if len(internal_reference_samples) < 10:
                    internal_reference_samples.append(word)
            words = [word for word in words if not is_internal_reference_key(word)]
            if not words:
                return
        if debug_mode and not any(word.casefold() in debug_word_set for word in words): return
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
                skipped_soup = BeautifulSoup(content, 'html.parser')
                has_entry_markup = bool(
                    skipped_soup.find('div', class_='entry')
                    or skipped_soup.find('span', class_='idm-g')
                )
                if has_entry_markup:
                    unexpected_parse_failures += 1
                    if len(unexpected_parse_samples) < 10:
                        unexpected_parse_samples.append(words[0] if words else "<empty key>")
                else:
                    non_dictionary_html_entries += 1

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

    if validate:
        validate_extraction_integrity(
            extractor.stats,
            mode,
            unexpected_parse_failures=unexpected_parse_failures,
        )

    empty_entry_placeholders_filtered = 0
    empty_entry_samples = []
    empty_entry_ids = set()
    renderable_entries = {}
    for word, ir_list in real_entries.items():
        for ir in ir_list:
            if entry_has_visible_content(ir):
                renderable_entries.setdefault(word, []).append(ir)
            elif id(ir) not in empty_entry_ids:
                empty_entry_ids.add(id(ir))
                empty_entry_placeholders_filtered += 1
                if len(empty_entry_samples) < 10:
                    empty_entry_samples.append(ir.get("word") or word)
    real_entries = renderable_entries

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
        term_tags, rule_pos = map_pos_metadata(ir['pos'])
        for label in ir['labels']:
            if label not in term_tags:
                term_tags.append(label)
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
    generate_metadata_files(
        output_dir,
        mode,
        ui_lang,
        dictionary_revision,
        source_revision=source_revision,
        debug_mode=debug_mode,
    )
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
        validate_yomitan_zip(
            zip_path,
            mode,
            ui_lang,
            allow_open=open_panels,
            expected_revision=dictionary_revision,
            expected_source_revision=source_revision,
        )
    if not keep_json:
        for f in [path for path in generated_files if os.path.basename(path).startswith("term_bank_")]:
            remove_generated_file(f, warn=True)

    print("\n=== Parser Stats ===")
    print(f"[*] Parsed HTML Entry Buffers: {parsed_html_entries}")
    print(f"[*] Non-dictionary HTML Pages Skipped: {non_dictionary_html_entries}")
    print(f"[*] Internal Reference Keys Skipped: {internal_reference_keys_skipped}")
    if internal_reference_samples:
        print(f"[*] Internal Reference Samples: {', '.join(internal_reference_samples)}")
    print(f"[*] Empty Entry Placeholders Filtered: {empty_entry_placeholders_filtered}")
    if empty_entry_samples:
        print(f"[*] Empty Entry Samples: {', '.join(empty_entry_samples)}")
    print(f"[*] Unexpected Parse Failures: {unexpected_parse_failures}")
    if unexpected_parse_samples:
        print(f"[*] Unexpected Failure Samples: {', '.join(unexpected_parse_samples)}")
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
    parser.add_argument('--revision', default=None,
                        help="Dictionary build revision shown by Yomitan. Defaults to today's date in YYYY.MM.DD format.")
    parser.add_argument('--debug', action='store_true',
                        help="Build only the default debug words and write readable JSON. Panels open by default in debug.")
    parser.add_argument('--test-words', default=None,
                        help="Comma- or semicolon-separated words for debug builds. Implies --debug.")
    parser.add_argument('--open-panels', action='store_true',
                        help="Force details panels to be open in the generated structured content.")
    parser.add_argument('--closed-panels', action='store_true',
                        help="Keep details panels closed even in debug builds.")
    parser.add_argument('--keep-json', action='store_true',
                        help="Keep term_bank JSON files after creating the zip. Debug builds keep them by default.")
    parser.add_argument('--discard-json', action='store_true',
                        help="Remove term_bank JSON files after creating the zip, even in debug builds.")
    parser.add_argument('--skip-validation', action='store_true',
                        help="Skip extraction-integrity and generated-zip validation.")
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
        revision=args.revision,
    )
