import os
import shutil
import subprocess
import xml.etree.ElementTree as ET
from PIL import Image
import difflib
import re

STATS = {
    "XML_MATCH": 0,
    "DIRECT_EXACT_MATCH": 0,
    "DIRECT_PREFIX_MATCH": 0,
    "SCORED_MATCH": 0,
    "FAILED": 0
}

def convert_apk(apk_path, mappings, synonyms, output_base_folder, theme_name, inherits_list):
    for k in STATS: STATS[k] = 0

    if not shutil.which("apktool"):
        print("Error: 'apktool' is not installed or not in PATH.")
        return None
    
    theme_root = os.path.join(output_base_folder, theme_name)
    icon_subfolder = os.path.join(theme_root, "apps", "512x512")
    places_subfolder = os.path.join(theme_root, "places", "512x512")
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    temp_dir = os.path.join(project_root, f"_temp_apktool_{theme_name}")
    
    if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
    os.makedirs(icon_subfolder, exist_ok=True)
    os.makedirs(places_subfolder, exist_ok=True)
    
    generate_index_theme(theme_name, theme_root, inherits_list)

    try:
        subprocess.run(
            ["apktool", "d", apk_path, "-o", temp_dir, "-f", "-s"], 
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT
        )
        available_files = index_all_images(temp_dir)

        processed_linux_names = set()
        processed_packages = set()
        total_mapped = 0
        appfilter_path = os.path.join(temp_dir, "assets", "appfilter.xml")
        
        if os.path.exists(appfilter_path):
            try:
                tree = ET.parse(appfilter_path)
                items = tree.getroot().findall('item')
                package_candidates = {}

                for item in items:
                    drawable_name = item.get('drawable')
                    component_raw = item.get('component')
                    if not drawable_name or not component_raw: continue
                    
                    resource_name = os.path.basename(drawable_name).replace("@drawable/", "").strip()
                    package_name = parse_component(component_raw)

                    if package_name not in package_candidates:
                        package_candidates[package_name] = []
                    
                    if resource_name not in package_candidates[package_name]:
                        package_candidates[package_name].append(resource_name)
                for pkg, linux_targets in mappings.items():
                    if pkg == "__COMMENT__": continue
                    
                    if pkg in package_candidates:
                        candidates = package_candidates[pkg]
                        criteria = generate_criteria(pkg, linux_targets, synonyms)
                        
                        best_candidate_name = None
                        best_candidate_score = -1

                        for cand_name in candidates:
                            score = calculate_file_score(cand_name, criteria)
                            
                            if score > best_candidate_score:
                                best_candidate_score = score
                                best_candidate_name = cand_name
                            
                            elif score == best_candidate_score and score > 0:
                                if len(cand_name) < len(best_candidate_name):
                                    best_candidate_name = cand_name

                        if best_candidate_name and best_candidate_name in available_files:
                            target_names, category = get_target_info(pkg, mappings)
                            dest_folder = places_subfolder if category == "places" else icon_subfolder
                            
                            count = save_one_source_to_many(available_files[best_candidate_name], dest_folder, target_names)
                            
                            if count > 0:
                                total_mapped += count
                                STATS["XML_MATCH"] += 1
                                for t in target_names: processed_linux_names.add(t)
                                processed_packages.add(pkg)

            except Exception as e:
                print(f"Error parsing XML: {e}")

        for key_source, targets in mappings.items():
            if key_source == "__COMMENT__": continue
            if key_source in processed_packages: continue
            target_list = targets if isinstance(targets, list) else [targets]
            missing_targets = [t for t in target_list if t not in processed_linux_names]
            
            if not missing_targets: continue
            wanted_names = generate_criteria(key_source, target_list, synonyms)
            match_found = False
            best_file_path = None
            for wanted in wanted_names:
                wanted = wanted.lower()
                if wanted in available_files:
                    best_file_path = available_files[wanted]
                    STATS["DIRECT_EXACT_MATCH"] += 1
                    match_found = True
                    break
            if not match_found:
                prefixes = ["ic_", "icon_", "app_", "launcher_"]
                for wanted in wanted_names:
                    for pre in prefixes:
                        candidate = f"{pre}{wanted}"
                        if candidate in available_files:
                            best_file_path = available_files[candidate]
                            STATS["DIRECT_PREFIX_MATCH"] += 1
                            match_found = True
                            break
                    if match_found: break
            if not match_found:
                best_score = 0
                
                for fname, fpath in available_files.items():
                    score = calculate_file_score(fname, wanted_names)
                    
                    if score > best_score:
                        best_score = score
                        best_file_path = fpath
                    elif score == best_score and score > 0:
                        if len(fname) < len(os.path.basename(best_file_path)):
                            best_file_path = fpath

                if best_score >= 50:
                    STATS["SCORED_MATCH"] += 1
                    match_found = True
                else:
                    best_file_path = None
            if match_found and best_file_path:
                is_place = key_source.startswith("resource_folder")
                dest_dir = places_subfolder if is_place else icon_subfolder
                
                success = save_one_source_to_many(best_file_path, dest_dir, missing_targets)
                if success > 0:
                    total_mapped += success
                    for t in missing_targets: processed_linux_names.add(t)
            else:
                STATS["FAILED"] += 1

        extra_count = collect_remaining_icons(available_files, icon_subfolder, processed_linux_names)

        return theme_root

    except subprocess.CalledProcessError:
        print("Error: Apktool failed.")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None
    finally:
        if os.path.exists(temp_dir):
            try: shutil.rmtree(temp_dir)
            except: pass

def generate_criteria(key_source, target_list, synonyms):
    """Generates search criteria based on mappings, synonyms, and package names."""
    criteria = []
    
    if "." in key_source:
        criteria.append(key_source.replace(".", "_"))
        parts = key_source.split('.')
        if len(parts) > 1:
            last = parts[-1]
            if last not in ["android", "app", "mobile"]: 
                criteria.append(last)
    else:
        criteria.append(key_source)

    if synonyms and key_source in synonyms:
        criteria.extend(synonyms[key_source])

    if key_source.startswith("resource_"):
        criteria.append(key_source.replace("resource_", ""))

    for t in target_list:
        clean_t = t.replace("org.", "").replace("com.", "").replace("kde.", "").replace("-", "_")
        if "." in clean_t: clean_t = clean_t.split(".")[-1]
        criteria.append(clean_t)
        
    return criteria

def calculate_file_score(filename, wanted_list):
    """Calculates the match score of a filename against a list of wanted terms."""
    filename = filename.lower()
    clean_fname = filename
    for p in ["ic_", "icon_", "app_", "launcher_"]:
        clean_fname = clean_fname.replace(p, "")
    
    max_s = 0

    for wanted in wanted_list:
        wanted = wanted.lower()
        score = 0
        
        if clean_fname == wanted:
            score = 1000
        
        else:
            tokens = clean_fname.replace("-", "_").split("_")
            if wanted in tokens:
                penalty = (len(tokens) - 1) * 20
                score = 800 - penalty
            
            else:
                parts = wanted.replace("-", "_").split("_")
                acronym = "".join([p[0] for p in parts]) if len(parts) > 1 else ""
                if acronym and clean_fname == acronym:
                    score = 600
                
                elif clean_fname.startswith(wanted):
                    score = 500
                
                elif wanted in clean_fname:
                     ratio = len(wanted) / len(clean_fname)
                     score = int(100 * ratio)
                     if not clean_fname.startswith(wanted): score -= 10
        
        if score > max_s: max_s = score
    return max_s

def get_target_info(package_name, mappings):
    if package_name in mappings:
        val = mappings[package_name]
        category = "places" if package_name.startswith("resource_folder") else "apps"
        targets = val if isinstance(val, list) else [val]
        return targets, category
    return [], "apps"

def save_one_source_to_many(source_path, dest_folder, target_names):
    count = 0
    try:
        with Image.open(source_path) as img:
            img.load()
            if img.mode != 'RGBA': base_img = img.convert('RGBA')
            else: base_img = img.copy()
            
            for name in target_names:
                try:
                    target_path = os.path.join(dest_folder, f"{name}.png")
                    base_img.save(target_path, "PNG")
                    count += 1
                except: pass
    except: return 0
    return count

def index_all_images(base_temp_dir):
    files_map = {}
    res_path = os.path.join(base_temp_dir, "res")
    if not os.path.exists(res_path): return {}
    priorities = ["mdpi", "hdpi", "xhdpi", "xxhdpi", "xxxhdpi", "nodpi"]
    all_dirs = []
    try: all_dirs = os.listdir(res_path)
    except: return {}
    
    sorted_dirs = [d for d in all_dirs if "drawable" in d and not any(p in d for p in priorities)]
    for p in priorities:
        sorted_dirs.extend([d for d in all_dirs if "drawable" in d and p in d])
            
    for folder in sorted_dirs:
        folder_path = os.path.join(res_path, folder)
        try:
            for f in os.listdir(folder_path):
                if f.endswith(".png") or f.endswith(".webp"):
                    name = os.path.splitext(f)[0].lower()
                    files_map[name] = os.path.join(folder_path, f)
        except: pass
    return files_map

def collect_remaining_icons(available_files, output_folder, already_processed):
    count = 0
    for name, source_path in available_files.items():
        if name in already_processed: continue
        try:
            with Image.open(source_path) as img:
                target_path = os.path.join(output_folder, f"{name}.png")
                img.save(target_path, "PNG")
                already_processed.add(name)
                count += 1
        except: pass
    return count

def parse_component(raw_component):
    try:
        return raw_component.replace("ComponentInfo{", "").replace("}", "").split("/")[0]
    except:
        return raw_component

def generate_index_theme(theme_name, theme_root, inherits_list):
    content = f"""[Icon Theme]
Name={theme_name}
Comment=Converted by IconBridge
Inherits={inherits_list}
Directories=apps/512x512,places/512x512

[apps/512x512]
Size=512
Context=Applications
Type=Fixed

[places/512x512]
Size=512
Context=Places
Type=Fixed
"""
    with open(os.path.join(theme_root, "index.theme"), "w") as f:
        f.write(content)