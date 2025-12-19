import os
import shutil
import json
import argparse
import re
from Scripts.converter import convert_apk

def sanitize_name(filename):
    name = os.path.splitext(os.path.basename(filename))[0]
    name = re.sub(r'[^a-zA-Z0-9]', '_', name)
    name = re.sub(r'_+', '_', name).strip('_')
    return name

def install_theme(source_path, theme_name):
    dest_base = os.path.expanduser("~/.local/share/icons")
    dest_path = os.path.join(dest_base, theme_name)

    if not os.path.exists(dest_base):
        try: os.makedirs(dest_base)
        except OSError: return

    if os.path.exists(dest_path):
        shutil.rmtree(dest_path)

    try:
        shutil.move(source_path, dest_path)
    except Exception as e:
        print(f"Error moving theme: {e}")

def main():
    parser = argparse.ArgumentParser(description="IconBridge")
    parser.add_argument("apk", help="Path to .apk file")
    parser.add_argument("-i", "--install", action="store_true", help="Install to ~/.local/share/icons")
    parser.add_argument("--inherits", default="breeze-dark,breeze,Adwaita,hicolor", 
                        help="Comma-separated list of theme parents (default: breeze-dark,breeze,Adwaita,hicolor)")
    
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_dir = os.path.join(base_dir, "Config")
    output_dir = os.path.join(base_dir, "Converted")
    
    mappings_path = os.path.join(config_dir, "mappings.json")
    synonyms_path = os.path.join(config_dir, "synonyms.json")

    if not os.path.exists(mappings_path):
        print("Error: Missing Config/mappings.json")
        return
    try:
        with open(mappings_path, 'r') as f: mappings = json.load(f)
    except json.JSONDecodeError:
        print("Error: Invalid mappings.json")
        return

    synonyms = {}
    if os.path.exists(synonyms_path):
        try:
            with open(synonyms_path, 'r') as f: synonyms = json.load(f)
        except json.JSONDecodeError:
            pass

    if not os.path.exists(output_dir): os.makedirs(output_dir)

    theme_name = sanitize_name(args.apk)
    result_path = convert_apk(args.apk, mappings, synonyms, output_dir, theme_name, args.inherits)

    if result_path and args.install:
        install_theme(result_path, theme_name)

if __name__ == "__main__":
    main()