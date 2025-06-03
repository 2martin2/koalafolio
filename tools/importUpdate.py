# This script updates PyQt5 imports in all Python files in the current directory.
# It replaces 'import PyQt5.<Module> as <alias>' with 'from PyQt5.<Module> import ...'
# and removes the alias usage from the code.

import os
import re
import pathlib


# get parent folder using pathlib
project_root = pathlib.Path(__file__).parents[1]

# PyQt module names
pyqt_modules = ["QtCore", "QtGui", "QtWidgets", "QtChart"]
# Regex patterns
pyqt_import_pattern = r"import PyQt5\.(?P<module>" + "|".join(pyqt_modules) + r") as (?P<alias>\w+)"
pyqt_element_pattern = r"(?P<alias>\w+)\.(?P<element>\w+)"

# Get all Python files in the current directory and subdirectorys
python_files = []
for root, dirs, files in os.walk(project_root):
    for file in files:
        if file.endswith(".py"):
            python_files.append(os.path.join(root, file))
# python_files = ["D:\git\koalafolio\koalafolio\gui\QLogger.py"]

for filename in python_files:
    print(f"\nProcessing file: {filename}")
    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Step 1: Find all aliases and their modules
    alias_list = []
    alias_module = {}
    for line in lines:
        match = re.search(pyqt_import_pattern, line)
        if match:
            module = match.group("module")
            alias = match.group("alias")
            if alias in alias_list:
                print(f"  [WARN] Alias '{alias}' is used multiple times in {filename}")
            else:
                alias_list.append(alias)
                alias_module[alias] = module
                print(f"  [INFO] Found alias '{alias}' for module '{module}'")

    # Step 2: Find all used elements for each alias
    elements_list = {alias: set() for alias in alias_list}
    for line in lines:
        for alias in alias_list:
            for match in re.finditer(pyqt_element_pattern, line):
                if match.group("alias") == alias:
                    element = match.group("element")
                    elements_list[alias].add(element)
                    print(f"  [INFO] Found element '{element}' for alias '{alias}'")

    # Step 3: Remove alias usage from code
    new_lines = []
    for line in lines:
        orig_line = line
        for alias in alias_list:
            # Remove alias usage (e.g., QtWidgets.QLabel -> QLabel)
            line = re.sub(rf"\b{alias}\.", "", line)
        new_lines.append(line)
        if orig_line != line:
            print(f"  [DEBUG] Updated line: {orig_line.strip()} -> {line.strip()}")

    # Step 4: Replace import lines with specific imports
    final_lines = []
    for line in new_lines:
        replaced = False
        for alias in alias_list:
            match = re.search(pyqt_import_pattern, line)
            if match and match.group("alias") == alias:
                module = alias_module[alias]
                elements = sorted(elements_list[alias])
                if elements:
                    import_line = f"from PyQt5.{module} import {', '.join(elements)}\n"
                    final_lines.append(import_line)
                    print(f"  [INFO] Replaced import for alias '{alias}' with: {import_line.strip()}")
                # Remove the old import line (do not append)
                replaced = True
                break
        if not replaced:
            final_lines.append(line)

    # Step 5: Write the updated lines back to the file
    with open(filename, "w", encoding="utf-8") as f:
        f.writelines(final_lines)
    print(f"  [DONE] Updated {filename}")







