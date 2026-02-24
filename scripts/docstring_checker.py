import ast
import os
import re
import sys

def parse_docstring_args(docstring):
    """Parses Google-style docstring to extract Args."""
    if not docstring:
        return set()

    args_section = re.search(r'Args:\n(.*?)(?:\n\s*\n|\Z)', docstring, re.DOTALL)
    if not args_section:
        return set()

    args_content = args_section.group(1)
    # Matches "  arg_name: description" or "  arg_name (type): description"
    arg_names = re.findall(r'^\s+(\w+)(?:\s*\(.*?\))?:', args_content, re.MULTILINE)
    return set(arg_names)

def check_file(filepath):
    """Checks a single file for docstring inconsistencies."""
    with open(filepath, 'r', encoding='utf-8') as f:
        try:
            tree = ast.parse(f.read(), filename=filepath)
        except SyntaxError:
            print(f"SyntaxError parsing {filepath}")
            return []

    errors = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Skip private functions if desired, or check them too.
            # For now, let's check everything that has a docstring.
            if not ast.get_docstring(node):
                continue

            docstring = ast.get_docstring(node)
            doc_args = parse_docstring_args(docstring)

            func_args = [arg.arg for arg in node.args.args]
            # Handle self and cls
            if func_args and func_args[0] in ('self', 'cls'):
                func_args = func_args[1:]

            func_args_set = set(func_args)

            missing_in_doc = func_args_set - doc_args
            missing_in_func = doc_args - func_args_set

            if missing_in_doc:
                errors.append(f"{filepath}:{node.lineno} Function '{node.name}' has args {missing_in_doc} missing from docstring.")
            if missing_in_func:
                errors.append(f"{filepath}:{node.lineno} Function '{node.name}' has args {missing_in_func} in docstring but not in signature.")

    return errors

def main():
    if len(sys.argv) < 2:
        print("Usage: python docstring_checker.py <directory>")
        sys.exit(1)

    directory = sys.argv[1]
    all_errors = []

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                all_errors.extend(check_file(filepath))

    if all_errors:
        print("Docstring Inconsistencies Found:")
        for error in all_errors:
            print(error)
        sys.exit(1)
    else:
        print("No docstring inconsistencies found.")

if __name__ == "__main__":
    main()
