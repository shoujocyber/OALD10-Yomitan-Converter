#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OALD 10 to Yomitan Dictionary Converter
Version: 1.2.0
Project URL: https://github.com/shoujocyber/OALD10-Yomitan-Converter
Description: 
    Converts unpacked MDX text of the Oxford Advanced Learner's Dictionary (10th Edition) 
    into the strict JSON format required by Yomitan. Features advanced data-cleaning, 
    multi-directional redirect resolution, Joint Primary Key deduplication, and auto-zipping.
"""

import json
import os
import re
import argparse
import zipfile
import glob
from bs4 import BeautifulSoup

# === Configuration & Metadata ===
VERSION = "1.2.1"
AUTHOR = "shoujocyber"

def generate_metadata_files(output_dir):
    """Generates the required index.json and tag_bank_1.json for Yomitan"""
    # 1. Generate index.json
    index_data = {
        "title": "Oxford Advanced Learner's Dictionary 10th",
        "format": 3,
        "revision": f"v{VERSION}",
        "sequenced": True,
        "author": AUTHOR,
        "url": "https://github.com/shoujocyber/OALD10-Yomitan-Converter",
        "description": "牛津高阶英汉双解词典(第10版)纯净版\nOxford Advanced Learner's Dictionary (10th Edition) En-Zh.\nHighly optimized and structured by OALD10-Yomitan-Converter.\nIncludes phrasal verbs, idioms, and deduplicated multi-source definitions."
    }
    with open(os.path.join(output_dir, 'index.json'), 'w', encoding='utf-8') as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)
    print("  [+] Created index.json")

    # 2. Generate tag_bank_1.json (Parts of Speech and Dictionary tags)
    tag_data = [
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
    with open(os.path.join(output_dir, 'tag_bank_1.json'), 'w', encoding='utf-8') as f:
        json.dump(tag_data, f, ensure_ascii=False, separators=(',', ':'))
    print("  [+] Created tag_bank_1.json")

def package_and_cleanup(output_dir):
    """Zips all JSON files and cleans up the temporary term banks"""
    zip_filename = f"OALD10_Yomitan_v{VERSION}.zip"
    zip_filepath = os.path.join(output_dir, zip_filename)
    
    index_file = os.path.join(output_dir, "index.json")
    tag_files = glob.glob(os.path.join(output_dir, "tag_bank_*.json"))
    term_banks = glob.glob(os.path.join(output_dir, "term_bank_*.json"))

    files_to_zip = []
    if os.path.exists(index_file): files_to_zip.append(index_file)
    files_to_zip.extend(tag_files)
    files_to_zip.extend(term_banks)

    if not files_to_zip:
        print("  [!] No files found to zip. Skipping packaging.")
        return

    print(f"\n📦 Packaging dictionary into: {zip_filename}")
    
    # 1. Compress files
    with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in files_to_zip:
            arcname = os.path.basename(file_path)
            zipf.write(file_path, arcname)
            
    print("🗑️  Cleaning up temporary JSON chunks...")

    # 2. Delete temporary term_bank_*.json files
    for file_path in term_banks:
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"  [!] Failed to delete {os.path.basename(file_path)}: {e}")

    print(f"✅ Packaging complete! Final file is ready: {zip_filepath}")

def parse_mdict_stable(input_file, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"=== OALD 10 to Yomitan Converter v{VERSION} ===")
    print(f"Input File: {input_file}")
    print(f"Output Dir: {output_dir}\n")
    
    # =========================================================
    # Phase 1: Parse Core Dictionary & Collect Redirects
    # =========================================================
    print("Phase 1/3: Building core vocabulary and extracting DOM structures...")
    real_entries = {}
    redirects = {}
    
    if not os.path.exists(input_file):
        print(f"❌ Error: Input file '{input_file}' not found. Please extract the MDX file first.")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        buffer = []
        for line in f:
            line = line.strip()
            if line == "</>":
                entry_text = "\n".join(buffer)
                buffer = []
                lines = entry_text.split('\n')
                if len(lines) < 2: continue
                
                words = [w.strip() for w in lines[0].split('|') if w.strip()]
                content = "".join(lines[1:])
                
                # Handle Redirect Pointers
                if "@@@LINK=" in content:
                    raw_target = content.replace("@@@LINK=", "").strip()
                    target = raw_target.split('|')[0].strip()
                    for w in words:
                        if w == target: continue
                        if w not in redirects: redirects[w] = []
                        if target not in redirects[w]: redirects[w].append(target)
                else:
                    # Parse standard dictionary entry
                    soup = BeautifulSoup(content, 'html.parser')
                    entries_list = []
                    
                    entry_blocks = soup.find_all('div', class_='entry')
                    if not entry_blocks:
                        entry_blocks = soup.find_all('span', class_='idm-g')

                    for entry_block in entry_blocks:
                        pos_tag = entry_block.find('span', class_='pos')
                        pos = pos_tag.get_text(strip=True) if pos_tag else ""
                        
                        # Assign 'idiom' tag to standalone idioms missing POS
                        if not pos and entry_block.name == 'span' and 'idm-g' in entry_block.get('class', []):
                            pos = "idiom"
                        
                        # Phonetics Extraction
                        uk_phon = entry_block.find('div', class_='phons_br')
                        us_phon = entry_block.find('div', class_='phons_n_am')
                        uk = uk_phon.find('span', class_='phon').get_text(strip=True) if uk_phon and uk_phon.find('span', class_='phon') else ""
                        us = us_phon.find('span', class_='phon').get_text(strip=True) if us_phon and us_phon.find('span', class_='phon') else ""
                        
                        if uk and us:
                            phonetic = f"UK/US: {uk}" if uk == us else f"UK: {uk} | US: {us}"
                        else:
                            phonetic = f"UK: {uk}" if uk else (f"US: {us}" if us else "")
                        
                        sense_strings = []
                        
                        # Global Meta Info (e.g., Grammar, Registers)
                        global_meta_parts = []
                        webtop = entry_block.find('div', class_='webtop')
                        if webtop:
                            for tag_name, chn_subtags in [('labels', ['labelx', 'chn']), ('grammar', []), ('use', ['uset', 'chn'])]:
                                g_node = webtop.find('span', class_=tag_name)
                                if g_node:
                                    chn_text = ""
                                    if chn_subtags:
                                        chn_node = g_node.find(chn_subtags[0]) or g_node.find('chn')
                                        if chn_node:
                                            chn_text = chn_node.get_text(separator='', strip=True)
                                            for c in g_node.find_all(chn_subtags + ['chn']): c.decompose()
                                    eng_text = g_node.get_text(separator=' ', strip=True).strip('()[] ')
                                    txt = f"{eng_text} {chn_text}".strip()
                                    if txt: global_meta_parts.append(f"【{txt}】")

                        senses = entry_block.find_all('li', class_='sense')
                        total_senses = len(senses)

                        for idx, sense in enumerate(senses):
                            # A. Extract Local Meta Info (Non-destructive)
                            local_meta_parts = []
                            sensetop = sense.find('span', class_='sensetop')
                            if sensetop:
                                for tag_name, chn_subtags in [('labels', ['labelx', 'chn']), ('grammar', []), ('use', ['uset', 'chn']), ('dis-g', ['dtxtx', 'chn'])]:
                                    l_node = sensetop.find('span', class_=tag_name)
                                    if l_node:
                                        chn_node = (l_node.find(chn_subtags[0]) if chn_subtags else None) or l_node.find('chn')
                                        chn_text = chn_node.get_text(separator='', strip=True) if chn_node else ""
                                        full_text = l_node.get_text(separator=' ', strip=True)
                                        eng_text = full_text.replace(chn_text, '') if chn_text else full_text
                                        eng_text = re.sub(r'\s+', ' ', eng_text.strip('()[] '))
                                        txt = f"{eng_text} {chn_text}".strip()
                                        if txt: local_meta_parts.append(f"【{txt}】")

                            # Separate Meta Inheritance for Idioms
                            idiom_prefix = ""
                            idm_g = sense.find_parent('span', class_='idm-g')
                            if idm_g:
                                idm_tag = idm_g.find('span', class_='idm')
                                if idm_tag:
                                    idiom_prefix = f"📌 {idm_tag.get_text(separator=' ', strip=True)}\n   "
                                
                                idiom_meta_parts = []
                                idm_webtop = idm_g.find('div', class_='webtop')
                                if idm_webtop:
                                    for tag_name, chn_subtags in [('labels', ['labelx', 'chn']), ('grammar', []), ('use', ['uset', 'chn'])]:
                                        g_node = idm_webtop.find('span', class_=tag_name)
                                        if g_node:
                                            chn_node = (g_node.find(chn_subtags[0]) if chn_subtags else None) or g_node.find('chn')
                                            chn_text = chn_node.get_text(separator='', strip=True) if chn_node else ""
                                            full_text = g_node.get_text(separator=' ', strip=True)
                                            eng_text = full_text.replace(chn_text, '') if chn_text else full_text
                                            eng_text = re.sub(r'\s+', ' ', eng_text.strip('()[] '))
                                            txt = f"{eng_text} {chn_text}".strip()
                                            if txt: idiom_meta_parts.append(f"【{txt}】")
                                combined_meta = idiom_meta_parts + local_meta_parts
                            else:
                                combined_meta = global_meta_parts + local_meta_parts
                            
                            meta_info = "".join(list(dict.fromkeys(combined_meta)))

                            # B. Extract Definitions & British/American Equivalents
                            variant_tags = sense.find_all(['div', 'span'], class_='variants')
                            var_parts = []
                            if variant_tags:
                                for var in variant_tags:
                                    for chn_tag in var.find_all(['labelx', 'chn']):
                                        chn_txt = chn_tag.get_text(strip=True)
                                        chn_tag.replace_with(f" {chn_txt} " if chn_txt else "")
                                    var_text = var.get_text(separator=' ', strip=True).strip('() ')
                                    var_text = re.sub(r'\s+', ' ', var_text) 
                                    var_text = var_text.replace("British English 英式英语", "英式对应词:")
                                    var_text = var_text.replace("North American English 美式英语", "美式对应词:")
                                    if var_text: var_parts.append(var_text)
                                    var.decompose()
                            
                            def_tag = sense.find('span', class_='def')
                            eng_def = def_tag.get_text(separator=' ', strip=True) if def_tag else ""
                            
                            if var_parts: eng_def = f"[{' | '.join(var_parts)}] {eng_def}".strip()
                                
                            cf_tags = sense.find_all('span', class_='cf')
                            main_cfs = [cf for cf in cf_tags if not cf.find_parent('ul', class_='examples')]
                            if main_cfs:
                                cf_text = " | ".join([cf.get_text(separator=' ', strip=True) for cf in main_cfs])
                                eng_def = f"【{cf_text}】 {eng_def}".strip()
                            
                            chn_def = ""
                            deft_tag = sense.find('deft')
                            if deft_tag:
                                for ai_tag in deft_tag.find_all('ai'):
                                    ai_text = ai_tag.get_text(separator='', strip=True)
                                    if ai_text: ai_tag.replace_with(f"[AI机翻] {ai_text}")
                                for leon_tag in deft_tag.find_all('leon'):
                                    leon_text = leon_tag.get_text(separator='', strip=True)
                                    if leon_text: leon_tag.replace_with(f"[个人审校] {leon_text}")
                                chn_def = deft_tag.get_text(separator=' ', strip=True)

                            # Cross-References (Clean English format)
                            xrefs_tag = sense.find('span', class_='xrefs')
                            if xrefs_tag:
                                prefix_tag = xrefs_tag.find('span', class_='prefix')
                                if prefix_tag:
                                    p_text = prefix_tag.get_text(strip=True).lower()
                                    if p_text in ['opposite', 'synonym', 'compare']:
                                        prefix_tag.replace_with(f"{p_text.capitalize()}: ")
                                    elif p_text == 'see also':
                                        prefix_tag.replace_with("See also: ")
                                    elif p_text == 'plural of':
                                        prefix_tag.replace_with("Plural of: ")
                                        
                                xref_text = xrefs_tag.get_text(separator=' ', strip=True)
                                xref_text = re.sub(r'\(\s+', '(', xref_text)
                                xref_text = re.sub(r'\s+\)', ')', xref_text)
                                xref_text = re.sub(r'\s+([.,])', r'\1', xref_text)
                                chn_def += f"\n   🔗 {xref_text}"
                            
                            if not eng_def and not chn_def: continue
                                
                            prefix = ""
                            if total_senses > 1:
                                prefix = f"{chr(0x2460 + idx)} " if idx < 20 else f"({idx+1}) "
                            
                            sense_text = f"■ {meta_info}\n" if meta_info else ""
                            sense_text += f"{prefix}{idiom_prefix}{eng_def}\n   {chn_def}".strip()
                            
                            # C. Extract and Rank Examples (Official > Proofread > AI > Pure EN)
                            ex_ul = sense.find('ul', class_='examples')
                            if ex_ul:
                                all_examples = []
                                for ex_li in ex_ul.find_all('li'):
                                    ex_span = ex_li.find('span', class_=['x', 'unx'])
                                    if ex_span:
                                        xt = ex_span.find(['xt', 'unxt'])
                                        ex_chn, priority = "", 0
                                        if xt:
                                            if xt.find('ai'):
                                                priority, ex_chn = 3, f"[机翻] {xt.find('ai').get_text(separator='', strip=True)}"
                                                xt.find('ai').decompose()
                                            elif xt.find('leon'):
                                                priority, ex_chn = 2, f"[个人审校] {xt.find('leon').get_text(separator='', strip=True)}"
                                                xt.find('leon').decompose()
                                            elif xt.find('oald'):
                                                priority, ex_chn = 1, f"[旧版] {xt.find('oald').get_text(separator='', strip=True)}"
                                                xt.find('oald').decompose()
                                            else:
                                                priority, ex_chn = 0, xt.get_text(separator='', strip=True)
                                            xt.decompose()
                                            
                                        ex_cf_prefix = ""
                                        ex_cfs = ex_li.find_all('span', class_='cf')
                                        if ex_cfs:
                                            cf_texts = [c.get_text(separator=' ', strip=True) for c in ex_cfs]
                                            ex_cf_prefix = f"[{' | '.join(cf_texts)}] "
                                            for c in ex_cfs: c.decompose()
                                        
                                        ex_eng = ex_span.get_text(separator=' ', strip=True)
                                        ex_eng = re.sub(r'\s+', ' ', ex_eng)
                                        ex_eng = re.sub(r'\s+([.,;?!:)])', r'\1', ex_eng)
                                        ex_eng = re.sub(r'(\()\s+', r'\1', ex_eng)
                                        
                                        if ex_chn:
                                            all_examples.append((priority, f"\n  ▼ {ex_cf_prefix}{ex_eng}\n    └ {ex_chn}"))
                                
                                all_examples.sort(key=lambda x: x[0])
                                for _, ex_text in all_examples[:5]:
                                    sense_text += ex_text
                                            
                            sense_strings.append(sense_text.strip())
                        
                        # D. Merge Definitions & Extract Phrasal Verbs list
                        combined_defs = "\n\n".join(sense_strings) if sense_strings else ""
                            
                        pv_aside = entry_block.find('aside', class_='phrasal_verb_links')
                        pv_g = entry_block.find('span', class_='pv-g')
                        
                        if pv_aside:
                            pvs = [pv.get_text(separator=' ', strip=True) for pv in pv_aside.find_all('span', class_='xh')]
                            if pvs: combined_defs += f"\n\n📌 相关短语动词: {', '.join(pvs)}"
                        elif not combined_defs and pv_g:
                            combined_defs = f"📌 相关短语形式: {pv_g.get_text(separator=' ', strip=True)}"
                        
                        if combined_defs:
                            entries_list.append({
                                "pos": pos,
                                "phon": phonetic,
                                "defs": [combined_defs.strip()] 
                            })
                            
                    if entries_list:
                        for w in words:
                            if w not in real_entries:
                                real_entries[w] = []
                            for entry_data in entries_list:
                                if entry_data not in real_entries[w]:
                                    real_entries[w].append(entry_data)
            else:
                buffer.append(line)
                
    print(f"  [✓] Phase 1 Complete: {len(real_entries)} core entries, {len(redirects)} redirects found.\n")
    
    # =========================================================
    # Phase 2: Resolve Multi-Directional Redirects
    # =========================================================
    print("Phase 2/3: Resolving multi-directional redirect chains...")
    resolved_redirects = {}
    dead_links_report = [] 
    
    for word, targets in redirects.items():
        valid_targets = []
        for t in targets:
            current_target = t
            visited = set([word])
            while current_target in redirects and current_target not in visited:
                visited.add(current_target)
                current_target = redirects[current_target][0] 
                
            if current_target in real_entries and current_target != word and current_target not in valid_targets:
                valid_targets.append(current_target)
                
        if valid_targets:
            resolved_redirects[word] = valid_targets
        else:
            if word not in real_entries:
                dead_links_report.append(f"{word}  ==points to==>  {' | '.join(targets)}")
            
    print(f"  [✓] Phase 2 Complete: Recovered {len(resolved_redirects)} derivative words.")

    if dead_links_report:
        report_path = os.path.join(output_dir, 'dead_links_report.txt')
        with open(report_path, 'w', encoding='utf-8') as df:
            df.write(f"=== OALD 10 Dead Links Report (Total: {len(dead_links_report)}) ===\n\n")
            df.write("\n".join(dead_links_report))
        print(f"  [!] Dumped dead links report to: {report_path}\n")

    # =========================================================
    # Phase 3: JSON Generation & Yomitan Data Aggregation
    # =========================================================
    print("Phase 3/3: Generating Yomitan data chunks (Applying Joint PK Deduplication)...")
    term_bank = []
    file_index = 1
    count = 0
    merged_duplicates_report = []
    
    def save_bank(data, index):
        out_path = os.path.join(output_dir, f'term_bank_{index}.json')
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=0)

    # 1. Output Core Entries
    for word, entry_list in real_entries.items():
        for entry_data in entry_list:
            # Core words have priority score 10
            term_entry = [word, entry_data["phon"], entry_data["pos"], "", 10, entry_data["defs"], count, ""]
            term_bank.append(term_entry)
            count += 1
            if len(term_bank) >= 10000:
                save_bank(term_bank, file_index)
                term_bank = []
                file_index += 1

    # 2. Output Derivative Entries (with Deduplication & Multi-source Merging)
    for word, root_targets in resolved_redirects.items():
        sig_to_targets = {}
        for root_target in root_targets:
            if root_target not in real_entries: continue
            for entry_data in real_entries[root_target]:
                pos = entry_data["pos"]
                for pure_def in entry_data["defs"]:
                    signature = (pos, pure_def)
                    if signature not in sig_to_targets:
                        sig_to_targets[signature] = []
                    if root_target not in sig_to_targets[signature]:
                        sig_to_targets[signature].append(root_target)
        
        pos_groups = {}
        for (pos, pure_def), targets in sig_to_targets.items():
            # Data Forensics: Catch redundant upstream data
            if len(targets) > 1:
                def_preview = pure_def.replace('\n', ' ')[:60] + "..."
                log_line = f"► Headword: [{word}]\n  └ POS: {pos}\n  └ Merged Sources: {' + '.join(targets)}\n  └ Definition: {def_preview}\n"
                if log_line not in merged_duplicates_report:
                    merged_duplicates_report.append(log_line)

            if pos not in pos_groups: pos_groups[pos] = []
            targets_str = " / ".join(targets)
            inherited_def = f"({word} 衍生自 → {targets_str})\n\n{pure_def}"
            pos_groups[pos].append(inherited_def)
                    
        for pos, defs in pos_groups.items():
            if not defs: continue
            inherited_def_block = "\n\n".join(defs)
            
            # Smart Phonetic Fallback
            if word in real_entries:
                exact_native = next((e for e in real_entries[word] if root_targets[0] in e["defs"][0]), None)
                base_phon = exact_native["phon"] if exact_native else real_entries[word][0]["phon"]
            else:
                base_phon = real_entries[root_targets[0]][0]["phon"]
                
            term_entry = [word, base_phon, pos, "", -10, [inherited_def_block], count, ""]
            term_bank.append(term_entry)
            count += 1
            if len(term_bank) >= 10000:
                save_bank(term_bank, file_index)
                term_bank = []
                file_index += 1

    if term_bank: 
        save_bank(term_bank, file_index)

    print(f"  [✓] Phase 3 Complete: Processed {count} total valid entries.\n")

    # 3. Output Data Forensics Report
    if merged_duplicates_report:
        report_path = os.path.join(output_dir, 'merged_duplicates_report.txt')
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("=== OALD 10 Deduplication & Merge Audit Report ===\n")
            f.write("Note: This list records extreme redundancies found in the original upstream database.\n\n")
            f.writelines(merged_duplicates_report)
        print(f"  [!] Dumped forensics report to: {report_path} (Intercepted {len(merged_duplicates_report)} upstream duplications)")

    # =========================================================
    # Phase 4: Metadata Generation & Auto-Zipping
    # =========================================================
    print("\nPhase 4: Generating metadata and packaging...")
    generate_metadata_files(output_dir)
    package_and_cleanup(output_dir)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert unpacked OALD10 MDX text to Yomitan JSON format.")
    parser.add_argument('-i', '--input', required=True, help="Path to the unpacked oaldpe.txt file")
    parser.add_argument('-o', '--output', default="./yomitan_out", help="Directory to save Yomitan JSON files (default: ./yomitan_out)")
    
    args = parser.parse_args()
    parse_mdict_stable(args.input, args.output)