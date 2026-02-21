import sys
import re

def fix_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Replace 3 or more newlines with 2
    new_content = re.sub(r'\n{4,}', '\n\n\n', content) # Keep max 2 blank lines (3 newlines)
    # Actually E303 says too many blank lines (3), meaning there are 4 \n characters in a row?
    # No, 3 blank lines means \n\n\n\n.
    # If flake8 says (3), it means 3 blank lines. Expected 2.

    # We want exactly 2 blank lines between top-level definitions.
    # So we want \n\n\n between code.

    new_content = re.sub(r'\n{4,}', '\n\n\n', content)

    if new_content != content:
        with open(filepath, 'w') as f:
            f.write(new_content)
            print(f"Fixed {filepath}")

for f in sys.argv[1:]:
    fix_file(f)
