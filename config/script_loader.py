"""
Script Loader - Automatically loads .ps1 scripts from the scripts folder.
"""

import os
import sys
import re


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def get_scripts_folder():
    """Get the path to the scripts folder, works for dev and PyInstaller."""
    return resource_path("scripts")


def parse_script_metadata(filepath):
    """Parse metadata from a .ps1 script file."""
    filename = os.path.splitext(os.path.basename(filepath))[0]
    metadata = {
        'name': filename,
        'description': 'No description',
        'style': 'Dark.TButton',
        'content': '',
        'interactive': False
    }
    
    try:
        content = None
        for encoding in ['utf-8-sig', 'utf-8', 'utf-16', 'latin-1']:
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    content = f.read()
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        if content is None:
            return metadata
        
        metadata['content'] = content
        
        name_match = re.search(r'^#\s*NAME\s*:\s*(.+)$', content, re.MULTILINE | re.IGNORECASE)
        if name_match:
            metadata['name'] = name_match.group(1).strip()
        
        desc_match = re.search(r'^#\s*DESCRIPTION\s*:\s*(.+)$', content, re.MULTILINE | re.IGNORECASE)
        if desc_match:
            metadata['description'] = desc_match.group(1).strip()
        
        style_match = re.search(r'^#\s*STYLE\s*:\s*(.+)$', content, re.MULTILINE | re.IGNORECASE)
        if style_match:
            style = style_match.group(1).strip()
            valid_styles = ['Dark.TButton', 'Warning.TButton', 'Danger.TButton', 'Success.TButton']
            if style in valid_styles:
                metadata['style'] = style
        
        interactive_match = re.search(r'^#\s*INTERACTIVE\s*:\s*(true|yes|1)$', content, re.MULTILINE | re.IGNORECASE)
        if interactive_match:
            metadata['interactive'] = True
        
        if re.search(r'\bRead-Host\b', content, re.IGNORECASE):
            metadata['interactive'] = True
        
    except Exception as e:
        print(f"Error reading script {filepath}: {e}")
    
    return metadata


def load_scripts_from_folder():
    """Load all .ps1 scripts from the scripts folder."""
    scripts_folder = get_scripts_folder()
    sections = []
    
    if not os.path.exists(scripts_folder):
        print(f"Scripts folder not found: {scripts_folder}")
        return sections
    
    try:
        items = sorted(os.listdir(scripts_folder))
    except Exception as e:
        print(f"Error reading scripts folder: {e}")
        return sections
    
    # Root-level scripts (not in a subfolder)
    root_scripts = []
    for item in items:
        item_path = os.path.join(scripts_folder, item)
        if os.path.isfile(item_path) and item.lower().endswith('.ps1'):
            metadata = parse_script_metadata(item_path)
            root_scripts.append((
                metadata['name'],
                metadata['content'],
                metadata['description'],
                metadata['style'],
                metadata['interactive']
            ))
    
    if root_scripts:
        sections.append(("📁 Scripts", root_scripts))
    
    # Subdirectory scripts
    for item in items:
        item_path = os.path.join(scripts_folder, item)
        
        if os.path.isdir(item_path):
            # Use raw folder name (no emoji prefix) for matching
            category_name = f"📁 {item}"
            category_scripts = []
            
            try:
                script_files = sorted(os.listdir(item_path))
            except:
                continue
            
            for script_file in script_files:
                if script_file.lower().endswith('.ps1'):
                    script_path = os.path.join(item_path, script_file)
                    metadata = parse_script_metadata(script_path)
                    
                    category_scripts.append((
                        metadata['name'],
                        metadata['content'],
                        metadata['description'],
                        metadata['style'],
                        metadata['interactive']
                    ))
            
            if category_scripts:
                sections.append((category_name, category_scripts))
    
    return sections


def get_all_script_sections():
    """Returns all script sections from the scripts folder."""
    return load_scripts_from_folder()