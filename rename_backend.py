import os
import re

def replace_in_file(filepath, replacements):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = content
    for old, new in replacements.items():
        new_content = new_content.replace(old, new)
        
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {filepath}")

def main():
    base_dir = '/Users/candemir/Desktop/Tekotek/Tekin Özel/EcomPro'
    backend_dir = os.path.join(base_dir, 'backend')
    old_app_dir = os.path.join(backend_dir, 'ecompro_backend')
    new_app_dir = os.path.join(backend_dir, 'ecommarj_backend')

    # Rename directory
    if os.path.exists(old_app_dir):
        os.rename(old_app_dir, new_app_dir)
        print(f"Renamed {old_app_dir} to {new_app_dir}")

    # Replacements list
    replacements = {
        'ecompro_backend': 'ecommarj_backend',
        'EcomPro': 'EcomMarj',
        'Ecompro': 'EcomMarj',
        'ecompro': 'ecommarj',
        'ECOMPRO': 'ECOMMARJ',
    }

    # Extensions to modify
    exts = ('.py', '.sh', '.yml', '.env', '.txt', '.md')

    # Walk and replace
    for root, dirs, files in os.walk(base_dir):
        # Skip node_modules, .git, frontend/src (already did frontend), .gemini
        if 'node_modules' in root or '.git' in root or '.gemini' in root or '.next' in root:
            continue

        for file in files:
            if file.endswith(exts):
                filepath = os.path.join(root, file)
                # Avoid touching the script itself
                if file == 'rename_backend.py':
                    continue
                replace_in_file(filepath, replacements)

if __name__ == "__main__":
    main()
