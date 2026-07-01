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

VERSION = "2.0.0"
AUTHOR = "shoujocyber"

# ==========================================
# 🌍 i18n Dictionary for UI & Metadata
# ==========================================
I18N_TEXT = {
    "zh": {
        "desc_bilingual": "牛津高阶英汉双解词典(第10版) 纯净优化版",
        "desc_mono": "牛津高阶词典(第10版) 沉浸英英版",
        "related_phrasal": "📌 相关短语: ",
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
        "related_phrasal": "📌 Related Phrasal Verbs: ",
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
DEBUG_MODE = False  
TEST_WORDS = ["read", "excited", "as", "afaic", "turn-around", "an", "a", "cry"]

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
        for eb in node.find_all(['span', 'a'], class_=['eb', 'ei', 'Ref']):
            eb.replace_with(f"⚑{eb.get_text(strip=True)}⚐")

    def _parse_panel(self, unbox):
        utype = unbox.get('unbox')
        title_en = utype.capitalize()
        title_zh = ""
        title_node = unbox.find('span', class_='box_title')
        if title_node:
            zh_node = title_node.find('unboxx')
            if zh_node:
                # Keep Chinese panel titles only if the UI language is set to 'zh'
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
                self.stats["vip_parsed"][utype] = self.stats["vip_parsed"].get(utype, 0) + 1
                    
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
                self.stats["vip_parsed"][utype] = self.stats["vip_parsed"].get(utype, 0) + 1
            
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
                            current_sec["items"].append({"en": self.clean_text(li.get_text()), "zh": zh_txt})
                if current_sec["items"] or current_sec["group_en"]: sections.append(current_sec)
                panel_data["data"] = sections
                self.stats["vip_parsed"][utype] = self.stats["vip_parsed"].get(utype, 0) + 1

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
                                    if el.name: cur_en.append(el.get_text(separator=' ', strip=True))
                                    else:
                                        if str(el).strip(): cur_en.append(str(el).strip())
                            
                            en_str = self.clean_text(" ".join(cur_en))
                            zh_str = self.clean_text(" ".join(cur_zh))
                            if en_str or zh_str:
                                li_chunks.append({"en": en_str, "zh": zh_str, "examples": []})
                            current_sec["items"].extend(li_chunks)
                if current_sec["items"] or current_sec["subtitle_en"]: sections.append(current_sec)
                panel_data["data"] = sections
                self.stats["vip_parsed"][utype] = self.stats["vip_parsed"].get(utype, 0) + 1

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
                                ex_data.append({"en": self.clean_text(unx.get_text()), "zh": ex_chn})
                            ex_ul.decompose()
                        syn_list.append({"highlight": eb_txt, "en": self.clean_text(defpara.get_text()), "zh": zh_txt, "examples": ex_data})
                panel_data["data"] = {"intro_en": intro_en, "intro_zh": intro_zh, "items": syn_list}
                self.stats["vip_parsed"][utype] = self.stats["vip_parsed"].get(utype, 0) + 1

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
                self.stats["vip_parsed"][utype] = self.stats["vip_parsed"].get(utype, 0) + 1

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
                            ex_en = self.clean_text(unx.get_text())
                        ex_node.decompose()
                    pos_txt = self.clean_text(li.get_text())
                    panel_data["data"].append({"word": eb_txt, "pos_info": pos_txt, "example_en": ex_en, "example_zh": ex_zh})
                self.stats["vip_parsed"][utype] = self.stats["vip_parsed"].get(utype, 0) + 1

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
                 self.stats["vip_parsed"][utype] = self.stats["vip_parsed"].get(utype, 0) + 1

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
                    panel_data["data"].append({"en": self.clean_text(ex.get_text()), "zh": zh_txt})
                self.stats["vip_parsed"][utype] = self.stats["vip_parsed"].get(utype, 0) + 1
                    
            elif utype == 'mlt':
                for ul in c_root.find_all('ul'):
                    items = [self.clean_text(li.get_text()) for li in ul.find_all('li')]
                    if items: panel_data["data"].append(items)
                self.stats["vip_parsed"][utype] = self.stats["vip_parsed"].get(utype, 0) + 1

            else:
                panel_data["data"] = self.clean_text(c_root.get_text())
                self.stats["fallback"][utype] = self.stats["fallback"].get(utype, 0) + 1

        except Exception as e:
            panel_data["data"] = self.clean_text(c_root.get_text())
            self.stats["errors"][utype] = self.stats["errors"].get(utype, 0) + 1

        return panel_data

    def parse_entry(self, html_content, word_list):
        word = word_list[0]
        aliases = [w for w in word_list if w != word] 

        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Purge all Chinese translation nodes immediately if Monolingual mode is active
        if self.mode == "mono":
            for zh_tag in soup.find_all(['chn', 'deft', 'uset', 'xt', 'unboxx', 'ubx', 'unxt', 'undt']):
                zh_tag.decompose()

        entry_blocks = soup.find_all('div', class_='entry')
        if not entry_blocks: entry_blocks = soup.find_all('span', class_='idm-g')
        if not entry_blocks: return []

        results = []
        for entry_block in entry_blocks:
            entry_ir = {
                "word": word, "aliases": aliases, "pos": "", "phonetics": {"uk": "", "us": ""},
                "labels": [], "senses": [], "panels": [],
                "global_see_also": [], "phrasal_verbs_links": []
            }

            pos_node = entry_block.find('span', class_='pos')
            entry_ir["pos"] = pos_node.get_text(strip=True) if pos_node else ""

            uk_phon = entry_block.find('div', class_='phons_br')
            us_phon = entry_block.find('div', class_='phons_n_am')
            if uk_phon and uk_phon.find('span', class_='phon'): entry_ir["phonetics"]["uk"] = uk_phon.find('span', class_='phon').get_text(strip=True)
            if us_phon and us_phon.find('span', class_='phon'): entry_ir["phonetics"]["us"] = us_phon.find('span', class_='phon').get_text(strip=True)

            symbols_div = entry_block.find('div', class_='symbols')
            if symbols_div:
                for span in symbols_div.find_all('span'):
                    for cls in span.get('class', []):
                        if cls.startswith('ox3ksym_') or cls.startswith('ox3ksymsub_'):
                            level = cls.split('_')[-1].upper()
                            entry_ir["labels"].extend(["Oxford3000", level])
                        elif cls.startswith('ox5ksym_') or cls.startswith('ox5ksymsub_'):
                            level = cls.split('_')[-1].upper()
                            entry_ir["labels"].extend(["Oxford5000", level])
                        elif 'opal_symbol' in cls:
                            entry_ir["labels"].append("OPAL")
            
            entry_ir["labels"] = list(dict.fromkeys(entry_ir["labels"]))

            for wo in entry_block.find_all('span', class_='unbox', unbox='wordorigin'):
                panel_data = self._parse_panel(wo)
                entry_ir["panels"].append(panel_data)
                wo.decompose()

            for sense in entry_block.find_all('li', class_='sense'):
                sense_data = {
                    "shortcut": "", "idiom": "", "phrasal_verb": "", 
                    "grammar": [], "eng": "", "chn": "", "examples": [],
                    "see_also": [], "panels": []
                }
                
                shcut_g = sense.find_parent(['span', 'div'], class_='shcut-g')
                if shcut_g and shcut_g.find('span', class_='shcut'): sense_data["shortcut"] = self.clean_text(shcut_g.find('span', class_='shcut').get_text())

                idm_g = sense.find_parent('span', class_='idm-g')
                if idm_g and idm_g.find('span', class_='idm'): sense_data["idiom"] = self.clean_text(idm_g.find('span', class_='idm').get_text())

                pv_g = sense.find_parent('span', class_='pv-g')
                if pv_g and pv_g.find('span', class_='pv'): sense_data["phrasal_verb"] = self.clean_text(pv_g.find('span', class_='pv').get_text())
                
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

                meta_nodes = sense.find_all('span', class_=['grammar', 'labels', 'dis-g', 'use'])
                if idm_g:
                    for gram in idm_g.find_all('span', class_=['grammar', 'labels', 'dis-g', 'use']):
                        if not gram.find_parent('li', class_='sense'): meta_nodes.insert(0, gram)

                seen_gram = set()
                for gram in meta_nodes:
                    if not gram.find_parent('span', class_='unbox') and not gram.find_parent('ul', class_='examples'):
                        chn = gram.find('chn')
                        chn_txt = chn.get_text(strip=True) if chn else ""
                        if chn: chn.decompose()
                        eng_txt = self.clean_text(gram.get_text())
                        combined = f"{eng_txt} {chn_txt}"
                        combined = re.sub(r'[()\[\]]', '', combined)
                        combined = re.sub(r'\s+', ' ', combined).strip()
                        if combined and combined not in seen_gram:
                            sense_data["grammar"].append(combined)
                            seen_gram.add(combined)
                        gram.decompose()
                
                def_tag = sense.find('span', class_='def')
                deft_tag = sense.find('deft')
                if def_tag: sense_data["eng"] = self.clean_text(def_tag.get_text())
                if deft_tag: 
                    for ai in deft_tag.find_all('ai'): ai.replace_with(ai.get_text())
                    sense_data["chn"] = self.clean_text(deft_tag.get_text())

                ex_list = []
                ex_ul = sense.find('ul', class_='examples')
                if ex_ul:
                    for ex_li in ex_ul.find_all('li'):
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
                            
                            cf_prefix = ""
                            cf_tags = ex_span.find_all('span', class_='cf')
                            if cf_tags:
                                cf_prefix = f"[{' | '.join([self.clean_text(c.get_text()) for c in cf_tags])}] "
                                for c in cf_tags: c.decompose()
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
    def __init__(self, ui_lang="zh"):
        self.ui_lang = ui_lang
        self.i18n = I18N_TEXT[ui_lang]
        
    def render_rich_text(self, text, prefix=""):
        if '⚑' not in text:
            return prefix + text
        content = []
        if prefix: content.append({"tag": "span", "content": prefix})
        parts = re.split(r'(⚑.*?⚐)', text)
        for part in parts:
            if part.startswith('⚑') and part.endswith('⚐'):
                content.append({"tag": "span", "style": {"fontWeight": "bold"}, "content": part[1:-1]})
            elif part:
                content.append({"tag": "span", "content": part})
        return content
        
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
                if data.get('en'): blocks.append({"tag": "div", "style": {"marginBottom": "2px"}, "content": self.render_rich_text(data['en'])})
                if data.get('zh'): blocks.append({"tag": "div", "style": {"marginBottom": "4px", "fontSize": "0.95em"}, "content": data['zh']})
                
        elif utype == 'cult' or utype == 'extra_examples':
            for item in data:
                blocks.append({"tag": "div", "style": {"marginBottom": "0px"}, "content": self.render_rich_text(item['en'], "▼ ")})
                if item['zh']: blocks.append({"tag": "div", "style": {"marginBottom": "4px", "fontSize": "0.95em"}, "content": f"└ {item['zh']}"})
                
        elif utype == 'verbforms':
            rows = []
            for item in data:
                phon_str = ""
                if item['phonetics'].get('uk') and item['phonetics'].get('uk') == item['phonetics'].get('us'): phon_str = f"UK/US: {item['phonetics']['uk']}"
                else: phon_str = " | ".join([f"{k.upper()}: {v}" for k, v in item['phonetics'].items() if v])
                rows.append({"tag": "tr", "content": [
                    {"tag": "td", "style": {"paddingRight": "12px", "paddingBottom": "2px"}, "content": item['form']},
                    {"tag": "td", "style": {"paddingRight": "12px", "paddingBottom": "2px", "fontWeight": "bold"}, "content": item['word']},
                    {"tag": "td", "style": {"paddingBottom": "2px"}, "content": phon_str}
                ]})
            blocks.append({"tag": "div", "style": {"marginTop": "2px", "marginBottom": "4px", "fontSize": "0.95em"}, "content": [{"tag": "table", "content": [{"tag": "tbody", "content": rows}]}]})
            
        elif utype == 'synonyms':
            if data['intro_en']: blocks.append({"tag": "div", "style": {"marginBottom": "2px"}, "content": self.render_rich_text(data['intro_en'])})
            if data['intro_zh']: blocks.append({"tag": "div", "style": {"marginBottom": "6px", "fontSize": "0.95em"}, "content": data['intro_zh']})
            for item in data['items']:
                line = []
                if item['highlight']: line.append({"tag": "span", "style": {"fontWeight": "bold", "color": "#0078D7"}, "content": f"{item['highlight']} "})
                if item['en']: line.append({"tag": "span", "content": item['en']})
                blocks.append({"tag": "div", "style": {"marginTop": "6px", "marginBottom": "2px"}, "content": line})
                if item['zh']: blocks.append({"tag": "div", "style": {"marginBottom": "4px", "fontSize": "0.95em"}, "content": item['zh']})
                for ex in item['examples']:
                    blocks.append({"tag": "div", "style": {"paddingLeft": "1.2em", "marginBottom": "0px"}, "content": f"▼ {ex['en']}"})
                    if ex['zh']: blocks.append({"tag": "div", "style": {"paddingLeft": "1.2em", "marginBottom": "4px", "fontSize": "0.95em"}, "content": f"└ {ex['zh']}"})
                    
        elif utype in ['langbank', 'which_word', 'british_american', 'wordfinder', 'wordfamily', 'grammar', 'more_about', 'express', 'vocab']:
            for sec in data:
                header = f"{sec['subtitle_en']} {sec['subtitle_zh']}".strip()
                if header: blocks.append({"tag": "div", "style": {"fontWeight": "bold", "color": "#0078D7", "marginTop": "6px", "marginBottom": "2px"}, "content": header})
                for item in sec['items']:
                    if item['en']: blocks.append({"tag": "div", "style": {"marginBottom": "2px"}, "content": f"■ {item['en']}"})
                    if item['zh']: blocks.append({"tag": "div", "style": {"marginBottom": "4px", "fontSize": "0.95em", "fontWeight": "bold"}, "content": item['zh']})
                    for ex in item['examples']:
                        blocks.append({"tag": "div", "style": {"paddingLeft": "1.2em", "marginBottom": "0px"}, "content": f"▼ {ex['en']}"})
                        if ex['zh']: blocks.append({"tag": "div", "style": {"paddingLeft": "1.2em", "marginBottom": "4px", "fontSize": "0.95em"}, "content": f"└ {ex['zh']}"})

        elif utype == 'colloc':
            for sec in data:
                header = sec['group_en']
                if sec['group_zh'] and sec['group_zh'] != sec['group_en']: header += f" ({sec['group_zh']})"
                if header: blocks.append({"tag": "div", "style": {"fontWeight": "bold", "color": "#0078D7", "marginTop": "6px", "marginBottom": "2px"}, "content": header})
                for item in sec['items']:
                    blocks.append({"tag": "div", "style": {"paddingLeft": "1.2em", "marginBottom": "0px"}, "content": f"• {item['en']}"})
                    if item['zh']: blocks.append({"tag": "div", "style": {"paddingLeft": "2.2em", "marginBottom": "4px", "fontSize": "0.95em"}, "content": item['zh']})

        elif utype == 'homophone':
            for item in data:
                blocks.append({"tag": "div", "content": [
                    {"tag": "span", "content": "• "},
                    {"tag": "span", "style": {"fontWeight": "bold"}, "content": item['word']},
                    {"tag": "span", "content": f" {item['pos_info']}"}
                ]})
                if item['example_en']: blocks.append({"tag": "div", "style": {"marginTop": "0px", "marginBottom": "0px"}, "content": f"▼ {item['example_en']}"})
                if item['example_zh']: blocks.append({"tag": "div", "style": {"marginBottom": "4px", "fontSize": "0.95em"}, "content": f"└ {item['example_zh']}"})

        elif utype == 'snippet':
            if isinstance(data, list):
                for sec in data:
                    blocks.append({"tag": "div", "content": f"[{sec['title']}] {', '.join(sec['items'])}"})
            
        elif utype == 'mlt':
            if isinstance(data, list):
                for items in data:
                    blocks.append({"tag": "div", "content": f"• {', '.join(items)}"})
                    
        return {
            "tag": "details",
            "open": True if DEBUG_MODE else False,
            "style": {"marginTop": "4px", "marginBottom": "2px", "fontSize": "0.9em"},
            "content": [
                {"tag": "summary", "style": {"cursor": "pointer", "fontWeight": "bold"}, "content": title},
                {"tag": "div", "style": {"marginTop": "4px", "paddingLeft": "10px", "marginLeft": "6px", "borderWidth": "0 0 0 2px", "borderStyle": "solid", "borderColor": "#4285f4"}, "content": blocks}
            ]
        }

    def render_entry(self, entry_ir):
        content_blocks = []
        
        phon_str = ""
        if entry_ir['phonetics'].get('uk') and entry_ir['phonetics'].get('uk') == entry_ir['phonetics'].get('us'): phon_str = f"UK/US: {entry_ir['phonetics']['uk']}"
        else: phon_str = " | ".join([f"{k.upper()}: {v}" for k, v in entry_ir['phonetics'].items() if v])
        if phon_str: content_blocks.append({"tag": "div", "style": {"whiteSpace": "pre-wrap", "marginBottom": "4px"}, "content": f"🔈 {phon_str}"})

        senses = entry_ir['senses']
        for i, sense in enumerate(senses):
            is_last = (i == len(senses) - 1)
            
            meta_parts = []
            if sense['shortcut']: meta_parts.append(f"[{sense['shortcut']}]")
            if sense['phrasal_verb']: meta_parts.append(f"[{sense['phrasal_verb']}]")
            for gram in sense['grammar']: meta_parts.append(f"[{gram}]")
            meta_str = " ".join(meta_parts)
            
            if sense['idiom']: content_blocks.append({"tag": "div", "style": {"fontWeight": "bold", "color": "#0078D7", "marginTop": "4px", "marginBottom": "2px"}, "content": f"📌 {sense['idiom']}"})
            
            prefix = (f"{chr(0x2460 + i)} " if i < 20 else f"({i+1}) ") if len(senses) > 1 else ""
            eng_line = []
            if prefix: eng_line.append({"tag": "span", "content": prefix})
            if meta_str: 
                eng_line.append({"tag": "span", "style": {"fontSize": "0.9em", "color": "#0078D7"}, "content": meta_str})
                eng_line.append({"tag": "span", "content": " "}) 
            if sense['eng']: 
                eng_line.append({"tag": "span", "content": sense['eng']})
            if eng_line: content_blocks.append({"tag": "div", "style": {"marginBottom": "2px"}, "content": eng_line})
            
            if sense['chn']: content_blocks.append({"tag": "div", "style": {"fontWeight": "bold", "marginBottom": "2px"}, "content": sense['chn']})
            
            for ex_idx, ex in enumerate(sense['examples']):
                content_blocks.append({"tag": "div", "style": {"paddingLeft": "1.2em", "marginBottom": "0px"}, "content": f"▼ {ex['en']}"})
                if ex['zh']: content_blocks.append({"tag": "div", "style": {"paddingLeft": "1.2em", "marginBottom": "4px", "fontSize": "0.95em"}, "content": f"└ {ex['zh']}"})

            if sense.get('see_also'):
                for sa in sense['see_also']:
                    sa_content = [{"tag": "span", "content": f"🔗 {sa['type']} "}]
                    for j, link in enumerate(sa['links']):
                        sa_content.append({"tag": "a", "href": f"?query={link}&wildcards=off", "content": link})
                        if j < len(sa['links']) - 1: sa_content.append(", ")
                    content_blocks.append({"tag": "div", "style": {"marginTop": "2px", "marginBottom": "2px"}, "content": sa_content})

            if sense.get('panels'):
                for p in sense['panels']:
                    node = self.render_unbox(p)
                    if node: content_blocks.append(node)

            if not is_last: content_blocks.append({"tag": "div", "style": {"paddingBottom": "12px"}, "content": ""})

        if entry_ir['global_see_also']:
            for sa in entry_ir['global_see_also']:
                sa_content = [{"tag": "span", "content": f"🔗 {sa['type']} "}]
                for j, link in enumerate(sa['links']):
                    sa_content.append({"tag": "a", "href": f"?query={link}&wildcards=off", "content": link})
                    if j < len(sa['links']) - 1: sa_content.append(", ")
                content_blocks.append({"tag": "div", "style": {"marginTop": "6px", "marginBottom": "2px"}, "content": sa_content})
                
        if entry_ir['phrasal_verbs_links']:
            pv_content = [{"tag": "span", "content": self.i18n["related_phrasal"]}]
            for j, pv in enumerate(entry_ir['phrasal_verbs_links']):
                pv_content.append({"tag": "a", "href": f"?query={pv}&wildcards=off", "content": pv})
                if j < len(entry_ir['phrasal_verbs_links']) - 1: pv_content.append(", ")
            content_blocks.append({"tag": "div", "style": {"marginTop": "6px"}, "content": pv_content})

        if entry_ir['panels']:
            content_blocks.append({"tag": "div", "style": {"marginTop": "8px"}, "content": ""})
            for p in entry_ir['panels']: 
                node = self.render_unbox(p)
                if node: content_blocks.append(node)

        return [{"type": "structured-content", "content": {"tag": "div", "content": content_blocks}}]

# ==========================================
# Module 3: Packaging & Control Flow
# ==========================================
def generate_metadata_files(output_dir, mode, ui_lang):
    i18n = I18N_TEXT[ui_lang]
    title_suffix = f" (Test)" if DEBUG_MODE else ""
    
    # Dynamically match the description based on the selected mode
    desc_text = i18n["desc_mono"] if mode == "mono" else i18n["desc_bilingual"]
    
    # Force a minimalist title to prevent bloating the Yomitan dictionary badge!
    # Edition distinctions are kept strictly in the description and zip filename.
    index_data = {
        "title": f"OALD 10{title_suffix}",
        "format": 3, "revision": f"v{VERSION}", "sequenced": True, "author": AUTHOR,
        "description": desc_text
    }
    with open(os.path.join(output_dir, 'index.json'), 'w', encoding='utf-8') as f: json.dump(index_data, f, ensure_ascii=False, indent=2)
    
    tags = i18n["tags"]
    tag_data = [
        ["noun", "partOfSpeech", 1, tags["noun"], 0],
        ["verb", "partOfSpeech", 1, tags["verb"], 0],
        ["adj", "partOfSpeech", 1, tags["adj"], 0],
        ["adv", "partOfSpeech", 1, tags["adv"], 0],
        ["pron", "partOfSpeech", 1, tags["pron"], 0],
        ["prep", "partOfSpeech", 1, tags["prep"], 0],
        ["conj", "partOfSpeech", 1, tags["conj"], 0],
        ["excl", "partOfSpeech", 1, tags["excl"], 0],
        ["det", "partOfSpeech", 1, tags["det"], 0],
        
        ["def-article", "partOfSpeech", 1, tags["def-article"], 0],
        ["indef-article", "partOfSpeech", 1, tags["indef-article"], 0],
        ["num", "partOfSpeech", 1, tags["num"], 0],
        ["ordinal-num", "partOfSpeech", 1, tags["ordinal-num"], 0],
        
        ["modal", "partOfSpeech", 1, tags["modal"], 0],
        ["aux", "partOfSpeech", 1, tags["aux"], 0],
        ["linking-v", "partOfSpeech", 1, tags["linking-v"], 0],
        ["phrasal-v", "partOfSpeech", 1, tags["phrasal-v"], 0],
        
        ["prefix", "partOfSpeech", 1, tags["prefix"], 0],
        ["suffix", "partOfSpeech", 1, tags["suffix"], 0],
        ["combining-form", "partOfSpeech", 1, tags["combining-form"], 0],
        ["inf-marker", "partOfSpeech", 1, tags["inf-marker"], 0],
        ["short-form", "partOfSpeech", 1, tags["short-form"], 0],
        ["abbr", "partOfSpeech", 1, tags["abbr"], 0],
        
        ["noun/adj", "partOfSpeech", 1, tags["noun/adj"], 0],
        ["idiom", "expression", 1, tags["idiom"], 0],
        ["symb", "partOfSpeech", 1, tags["symb"], 0],
        
        ["A1", "frequent", 2, tags["A1"], 0],
        ["A2", "frequent", 2, tags["A2"], 0],
        ["B1", "frequent", 2, tags["B1"], 0],
        ["B2", "frequent", 2, tags["B2"], 0],
        ["C1", "frequent", 2, tags["C1"], 0],
        ["C2", "frequent", 2, tags["C2"], 0],

        ["Oxford3000", "popular", 3, tags["Oxford3000"], 0],
        ["Oxford5000", "popular", 3, tags["Oxford5000"], 0],
        ["OPAL", "popular", 3, tags["OPAL"], 0],
        
        ["redirect", "search", -5, tags["redirect"], 0]
    ]
    with open(os.path.join(output_dir, 'tag_bank_1.json'), 'w', encoding='utf-8') as f: json.dump(tag_data, f, ensure_ascii=False, separators=(',', ':'))

def package_dictionary(input_file, output_dir, mode, ui_lang):
    if not os.path.exists(output_dir): os.makedirs(output_dir)
    print(f"=== OALD 10 to Yomitan V{VERSION} Engine ===")
    print(f"[*] Dictionary Mode:  {mode.upper()}")
    print(f"[*] UI Language:      {ui_lang.upper()}")
    
    extractor = OaldExtractor(mode=mode, ui_lang=ui_lang)
    renderer = YomitanRenderer(ui_lang=ui_lang)
    
    real_entries = {}
    redirects = {}
    
    with open(input_file, 'r', encoding='utf-8') as f: total_lines = sum(1 for _ in f)

    with open(input_file, 'r', encoding='utf-8') as f:
        buffer = []
        for line in tqdm(f, total=total_lines, desc="Processing Data"):
            line = line.strip()
            if line == "</>":
                entry_text = "\n".join(buffer)
                buffer = []
                lines = entry_text.split('\n')
                if len(lines) < 2: continue
                words = [w.strip() for w in lines[0].split('|') if w.strip()]
                
                if DEBUG_MODE and not any(tw in words for tw in TEST_WORDS): continue
                content = "".join(lines[1:])
                
                if "@@@LINK=" in content:
                    target = content.replace("@@@LINK=", "").strip().split('|')[0].strip()
                    for w in words:
                        if w != target:
                            if w not in redirects: redirects[w] = []
                            redirects[w].append(target)
                else:
                    ir_list = extractor.parse_entry(content, words)
                    if ir_list:
                        for w in words:
                            if w not in real_entries: real_entries[w] = []
                            real_entries[w].extend(ir_list)
            else:
                buffer.append(line)

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
        with open(os.path.join(output_dir, f'term_bank_{idx}.json'), 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=0)

    pos_mapping = {
        "verb": "v", "noun": "n", "adjective": "adj", "adverb": "adv",
        "pronoun": "pron", "preposition": "prep", "conjunction": "conj",
        "phrasal verb": "v_phr"
    }

    # UI Polish: Elegant and concise tag naming
    visual_tag_map = {
        "noun": "noun", "verb": "verb", "adjective": "adj", "adverb": "adv",
        "pronoun": "pron", "preposition": "prep", "conjunction": "conj",
        "exclamation": "excl", "determiner": "det",
        "definite article": "def-article", "indefinite article": "indef-article",
        "number": "num", "ordinal number": "ordinal-num",
        "modal verb": "modal", "auxiliary verb": "aux", "linking verb": "linking-v",
        "phrasal verb": "phrasal-v", "prefix": "prefix", "suffix": "suffix",
        "combining form": "combining-form", "infinitive marker": "inf-marker",
        "short form": "short-form", "abbreviation": "abbr",
        "idiom": "idiom", "symbol": "symb", "n.": "noun", "adj.": "adj", "n., adj.": "noun/adj"
    }

    print("\n📦 Building Yomitan database (with deduplication)...")
    for word, ir_list in real_entries.items():
        unique_irs = []
        seen_hashes = set()
        for ir in ir_list:
            ir_copy = ir.copy()
            ir_copy.pop('word', None)
            ir_copy.pop('aliases', None) 
            ir_hash = json.dumps(ir_copy, sort_keys=True)
            if ir_hash not in seen_hashes:
                seen_hashes.add(ir_hash)
                unique_irs.append(ir)
                
        for ir in unique_irs:
            final_defs = renderer.render_entry(ir)
            
            term_tags = []
            
            raw_pos = ir['pos'].lower()
            if raw_pos in visual_tag_map: term_tags.append(visual_tag_map[raw_pos])
            elif raw_pos: term_tags.append(raw_pos.replace(" ", "-"))
                
            term_tags.extend(ir['labels']) 
            
            rule_pos = pos_mapping.get(raw_pos, "")

            term_bank.append([word, "", " ".join(term_tags), rule_pos, 10, final_defs, count, ""])
            count += 1
            if len(term_bank) >= 10000: save_bank(term_bank, file_index); term_bank = []; file_index += 1

    for word, root_targets in resolved_redirects.items():
        if not root_targets: continue
        redirect_content = [[t, ["redirect"]] for t in list(dict.fromkeys(root_targets))]
        term_bank.append([word, "", "non-lemma", "", -10, redirect_content, count, ""])
        count += 1
        if len(term_bank) >= 10000: save_bank(term_bank, file_index); term_bank = []; file_index += 1

    if term_bank: save_bank(term_bank, file_index)
    generate_metadata_files(output_dir, mode, ui_lang)

    print(f"\n📊 Generating data audit report...")
    with open(os.path.join(output_dir, 'build_report.txt'), 'w', encoding='utf-8') as f:
        f.write(f"=== OALD10 to Yomitan V{VERSION} Audit Report ===\n")
        f.write(f"Completion Time: {time.ctime()}\n\n")
        f.write("[1] Successfully parsed advanced structured panels:\n")
        for k, v in sorted(extractor.stats["vip_parsed"].items(), key=lambda x: -x[1]):
            f.write(f"  - {k.ljust(20)}: {v} times\n")
        
        f.write("\n[2] Fallback to plain text for undefined panels:\n")
        if not extractor.stats["fallback"]: f.write("  - (None! All panels gracefully parsed!)\n")
        for k, v in sorted(extractor.stats["fallback"].items(), key=lambda x: -x[1]):
            f.write(f"  - {k.ljust(20)}: {v} times\n")
            
        f.write("\n[3] Crash interceptions due to format anomalies:\n")
        if not extractor.stats["errors"]: f.write("  - (None! Data is perfect!)\n")
        for k, v in sorted(extractor.stats["errors"].items(), key=lambda x: -x[1]):
            f.write(f"  - {k.ljust(20)}: {v} times\n")

    # Minimalist scenario-based file naming
    zip_filename = f"OALD10_Yomitan_Test" if DEBUG_MODE else f"OALD10_Yomitan_V{VERSION}"
    if mode == "mono" and ui_lang == "en":
        zip_filename += "_Global.zip"        # Global English-only edition
    elif mode == "mono":
        zip_filename += "_Immersion.zip"     # Immersion edition for Chinese learners (EN-EN + ZH tags)
    elif ui_lang == "en":
        zip_filename += "_EN_Tags.zip"       # Bilingual edition with English UI tags
    else:
        zip_filename += ".zip"               # Default standard bilingual edition
    
    print(f"\n✅ Compressing dictionary: {zip_filename}")
    with zipfile.ZipFile(os.path.join(output_dir, zip_filename), 'w', zipfile.ZIP_DEFLATED) as zipf:
        for f in glob.glob(os.path.join(output_dir, "*.json")): zipf.write(f, os.path.basename(f))
    for f in glob.glob(os.path.join(output_dir, "term_bank_*.json")):
        try: os.remove(f)
        except: pass
    
    print(f"\n🎉 Done! Please check {output_dir}/build_report.txt for the data health report!")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="OALD 10 to Yomitan Dictionary Builder")
    parser.add_argument('-i', '--input', required=True, help="Input file path (e.g., oaldpe.txt)")
    parser.add_argument('-o', '--output', default="./yomitan_v2", help="Output folder path")
    parser.add_argument('-m', '--mode', choices=['bilingual', 'mono'], default='bilingual', 
                        help="Dictionary content mode: 'bilingual' (EN-ZH) or 'mono' (EN-EN)")
    parser.add_argument('-u', '--ui-lang', choices=['zh', 'en'], default='zh', 
                        help="Language for UI elements like tags and descriptions")
    args = parser.parse_args()
    
    package_dictionary(args.input, args.output, args.mode, args.ui_lang)