"""
OALD 10 to Yomitan Dictionary Converter
=======================================
An advanced script to deeply parse, clean, and restructure the Oxford Advanced 
Learner's Dictionary (10th Ed) EN-ZH MDX text dump into Yomitan JSON format.

Features:
- Handles multi-level chained redirects.
- Extracts global/local meta tags and syntactic frames.
- Prioritizes official translation examples over AI/proofread ones.
- Rescues idiom-only and phrasal-verb-only stub entries.
"""

import json
import os
import re
from bs4 import BeautifulSoup

# ==========================================
# User Configuration (用户路径配置区)
# ==========================================
INPUT_FILE = r"oaldpe.txt"          # The unpacked MDX text file
OUTPUT_DIR = r"yomitan_out"         # Directory to save the generated JSON files

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def parse_mdict_stable():
    print("Phase 1: Building Core Dictionary & Collecting Redirects...")
    real_entries = {}
    redirects = {}
    
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found. Please unpack the MDX file first.")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        buffer = []
        for line in f:
            line = line.strip()
            if line == "</>":
                entry_text = "\n".join(buffer)
                buffer = []
                lines = entry_text.split('\n')
                if len(lines) < 2: continue
                
                word = lines[0].strip()
                content = "".join(lines[1:])
                
                # Store redirects for Phase 2 resolution
                if "@@@LINK=" in content:
                    target = content.replace("@@@LINK=", "").strip()
                    redirects[word] = target
                else:
                    soup = BeautifulSoup(content, 'html.parser')
                    entries_list = [] 
                    
                    # Target standard entries (div.entry) or standalone idioms (span.idm-g)
                    entry_blocks = soup.find_all('div', class_='entry')
                    if not entry_blocks:
                        entry_blocks = soup.find_all('span', class_='idm-g')

                    for entry_block in entry_blocks:
                        pos_tag = entry_block.find('span', class_='pos')
                        pos = pos_tag.get_text(strip=True) if pos_tag else ""
                        
                        # Fallback for standalone idioms without explicit Part of Speech
                        if not pos and entry_block.name == 'span' and 'idm-g' in entry_block.get('class', []):
                            pos = "idiom"
                        
                        # Extract and merge Phonetics (UK / US)
                        uk_phon = entry_block.find('div', class_='phons_br')
                        us_phon = entry_block.find('div', class_='phons_n_am')
                        uk = uk_phon.find('span', class_='phon').get_text(strip=True) if uk_phon and uk_phon.find('span', class_='phon') else ""
                        us = us_phon.find('span', class_='phon').get_text(strip=True) if us_phon and us_phon.find('span', class_='phon') else ""
                        
                        if uk and us:
                            phonetic = f"UK/US: {uk}" if uk == us else f"UK: {uk} | US: {us}"
                        else:
                            phonetic = f"UK: {uk}" if uk else (f"US: {us}" if us else "")
                        
                        sense_strings = []
                        
                        # --- Global Meta Information Extraction ---
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
                                            # Decompose to prevent duplicate extraction in local senses
                                            for c in g_node.find_all(chn_subtags + ['chn']): c.decompose()
                                    eng_text = g_node.get_text(separator=' ', strip=True).strip('()[] ')
                                    txt = f"{eng_text} {chn_text}".strip()
                                    if txt: global_meta_parts.append(f"【{txt}】")

                        senses = entry_block.find_all('li', class_='sense')
                        total_senses = len(senses)

                        for idx, sense in enumerate(senses):
                            # --- Local Meta Information Extraction ---
                            local_meta_parts = []
                            for tag_name, chn_subtags in [('labels', ['labelx', 'chn']), ('grammar', []), ('use', ['uset', 'chn']), ('dis-g', ['dtxtx', 'chn'])]:
                                l_node = sense.find('span', class_=tag_name)
                                if l_node:
                                    chn_text = ""
                                    if chn_subtags:
                                        chn_node = l_node.find(chn_subtags[0]) or l_node.find('chn')
                                        if chn_node:
                                            chn_text = chn_node.get_text(separator='', strip=True)
                                            for c in l_node.find_all(chn_subtags + ['chn']): c.decompose()
                                    eng_text = l_node.get_text(separator=' ', strip=True).strip('()[] ')
                                    txt = f"{eng_text} {chn_text}".strip()
                                    if txt: local_meta_parts.append(f"【{txt}】")

                            # Merge global and local meta tags, removing duplicates while preserving order
                            combined_meta = global_meta_parts + local_meta_parts
                            meta_info = "".join(list(dict.fromkeys(combined_meta)))

                            # --- Core Definitions & Syntactic Frames ---
                            def_tag = sense.find('span', class_='def')
                            eng_def = def_tag.get_text(separator=' ', strip=True) if def_tag else ""
                            
                            cf_tags = sense.find_all('span', class_='cf')
                            # Filter out 'cf' tags that belong to example sentences
                            main_cfs = [cf for cf in cf_tags if not cf.find_parent('ul', class_='examples')]
                            if main_cfs:
                                cf_text = " | ".join([cf.get_text(separator=' ', strip=True) for cf in main_cfs])
                                eng_def = f"【{cf_text}】 {eng_def}".strip()
                            
                            chn_def = ""
                            deft_tag = sense.find(['deft', 'chn'])
                            if deft_tag:
                                # Downgrade AI & Proofread tags for better UX
                                for ai_tag in deft_tag.find_all('ai'):
                                    ai_text = ai_tag.get_text(separator='', strip=True)
                                    if ai_text: ai_tag.replace_with(f"[AI机翻] {ai_text}")
                                for leon_tag in deft_tag.find_all('leon'):
                                    leon_text = leon_tag.get_text(separator='', strip=True)
                                    if leon_text: leon_tag.replace_with(f"[个人审校] {leon_text}")
                                    
                                chn_def = deft_tag.get_text(separator=' ', strip=True)

                            # --- Cross-References (Synonyms/Related Words) ---
                            xrefs_tag = sense.find('span', class_='xrefs')
                            if xrefs_tag:
                                xref_text = xrefs_tag.get_text(separator=' ', strip=True)
                                xref_text = re.sub(r'\s+([.,])', r'\1', xref_text)
                                chn_def += f"\n   🔗 {xref_text}"
                            
                            if not eng_def and not chn_def:
                                continue
                                
                            prefix = ""
                            if total_senses > 1:
                                prefix = f"{chr(0x2460 + idx)} " if idx < 20 else f"({idx+1}) "
                                
                            # --- Trace upwards to capture enclosing Idiom groupings ---
                            idiom_prefix = ""
                            idm_g = sense.find_parent('span', class_='idm-g')
                            if idm_g:
                                idm_tag = idm_g.find('span', class_='idm')
                                if idm_tag:
                                    idiom_text = idm_tag.get_text(separator=' ', strip=True)
                                    idiom_prefix = f"📌 {idiom_text}\n   "
                            
                            sense_text = ""
                            if meta_info: sense_text += f"■ {meta_info}\n"
                            sense_text += f"{prefix}{idiom_prefix}{eng_def}\n   {chn_def}".strip()
                            
                            # --- Extract & Sort Examples ---
                            ex_ul = sense.find('ul', class_='examples')
                            if ex_ul:
                                all_examples = []
                                
                                for ex_li in ex_ul.find_all('li'):
                                    ex_span = ex_li.find('span', class_=['x', 'unx'])
                                    if ex_span:
                                        xt = ex_span.find(['xt', 'unxt'])
                                        ex_chn = ""
                                        priority = 0 # 0 (Official) is highest priority
                                        
                                        if xt:
                                            if xt.find('ai'):
                                                priority = 3
                                                ai_tag = xt.find('ai')
                                                ex_chn = f"[机翻] {ai_tag.get_text(separator='', strip=True)}"
                                                ai_tag.decompose()
                                            elif xt.find('leon'):
                                                priority = 2
                                                leon_tag = xt.find('leon')
                                                ex_chn = f"[个人审校] {leon_tag.get_text(separator='', strip=True)}"
                                                leon_tag.decompose()
                                            elif xt.find('oald'):
                                                priority = 1
                                                oald_tag = xt.find('oald')
                                                ex_chn = f"[旧版] {oald_tag.get_text(separator='', strip=True)}"
                                                oald_tag.decompose()
                                            else:
                                                priority = 0
                                                ex_chn = xt.get_text(separator='', strip=True)
                                                
                                            xt.decompose() 
                                            
                                        # Prefix example-specific syntactic frames
                                        ex_cf_prefix = ""
                                        ex_cfs = ex_li.find_all('span', class_='cf')
                                        if ex_cfs:
                                            cf_texts = [c.get_text(separator=' ', strip=True) for c in ex_cfs]
                                            ex_cf_prefix = f"[{' | '.join(cf_texts)}] "
                                            for c in ex_cfs: c.decompose()
                                        
                                        # Clean up English spacing and punctuation
                                        ex_eng = ex_span.get_text(separator=' ', strip=True)
                                        ex_eng = re.sub(r'\s+', ' ', ex_eng)
                                        ex_eng = re.sub(r'\s+([.,;?!:)])', r'\1', ex_eng)
                                        ex_eng = re.sub(r'(\()\s+', r'\1', ex_eng)
                                        ex_eng = f"{ex_cf_prefix}{ex_eng}".strip()
                                        
                                        if ex_chn:
                                            all_examples.append((priority, f"\n  ▼ {ex_eng}\n    └ {ex_chn}"))
                                
                                # Sort by priority (0->1->2->3) and keep the top 5
                                all_examples.sort(key=lambda x: x[0])
                                for _, ex_text in all_examples[:5]:
                                    sense_text += ex_text
                                            
                            sense_strings.append(sense_text.strip())
                        
                        # --- Final Assembly per Part of Speech ---
                        combined_defs = ""
                        if sense_strings:
                            combined_defs = "\n\n".join(sense_strings)
                            
                        # Rescue stub entries that only contain Phrasal Verbs
                        pv_aside = entry_block.find('aside', class_='phrasal_verb_links')
                        if pv_aside:
                            pvs = [pv.get_text(separator=' ', strip=True) for pv in pv_aside.find_all('span', class_='xh')]
                            if pvs:
                                if combined_defs:
                                    combined_defs += f"\n\n📌 相关短语动词 (Phrasal Verbs): {', '.join(pvs)}"
                                else:
                                    combined_defs = f"📌 请查看相关短语动词 (See Phrasal Verbs): {', '.join(pvs)}"
                        
                        if combined_defs:
                            entries_list.append({
                                "pos": pos,
                                "phon": phonetic,
                                "defs": [combined_defs] 
                            })
                            
                    if entries_list:
                        real_entries[word] = entries_list
            else:
                buffer.append(line)
                
    print(f"Phase 1 Complete. Core entries: {len(real_entries)}, Raw redirects: {len(redirects)}")
    
    print("Phase 2: Resolving Chained Redirects...")
    resolved_redirects = {}
    dead_links_report = [] 
    
    for word, target in redirects.items():
        current_target = target
        visited = set([word])
        
        # Traverse multi-level redirects
        while current_target in redirects and current_target not in visited:
            visited.add(current_target)
            current_target = redirects[current_target]
            
        if current_target in real_entries:
            resolved_redirects[word] = current_target
        else:
            dead_links_report.append(f"{word}  ==指向==>  {current_target}")
            
    print(f"Recovered derived words: {len(resolved_redirects)}. Dead links filtered: {len(dead_links_report)}.")
    
    # Export dead links report
    if dead_links_report:
        report_path = os.path.join(OUTPUT_DIR, 'dead_links_report.txt')
        with open(report_path, 'w', encoding='utf-8') as df:
            df.write(f"=== OALD 10 Dead Links Report ({len(dead_links_report)} total) ===\n\n")
            df.write("\n".join(dead_links_report))
        print(f"📁 Dead links report generated: {report_path}")

    print("Phase 3: Generating Yomitan JSON Banks...")
    term_bank = []
    file_index = 1
    count = 0
    
    def save_bank(data, index):
        out_path = os.path.join(OUTPUT_DIR, f'term_bank_{index}.json')
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=0)

    # Output core entries
    for word, entry_list in real_entries.items():
        for entry_data in entry_list:
            term_entry = [word, entry_data["phon"], entry_data["pos"], "", 0, entry_data["defs"], count, ""]
            term_bank.append(term_entry)
            count += 1
            if len(term_bank) >= 10000:
                save_bank(term_bank, file_index)
                print(f"Generated term_bank_{file_index}.json (Progress: {count})")
                term_bank = []
                file_index += 1
                
    # Output resolved redirect entries
    for word, root_target in resolved_redirects.items():
        for entry_data in real_entries[root_target]:
            inherited_def = f"({word} 衍生自 → {root_target})\n\n" + entry_data["defs"][0]
            term_entry = [word, entry_data["phon"], entry_data["pos"], "", 0, [inherited_def], count, ""]
            term_bank.append(term_entry)
            count += 1
            if len(term_bank) >= 10000:
                save_bank(term_bank, file_index)
                print(f"Generated term_bank_{file_index}.json (Progress: {count})")
                term_bank = []
                file_index += 1

    if term_bank: 
        save_bank(term_bank, file_index)
        print(f"Generated term_bank_{file_index}.json (Final batch)")

    print(f"\nAll done! Total valid entries: {count}")

if __name__ == "__main__":
    parse_mdict_stable()
