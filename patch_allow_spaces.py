filepath = r'E:\GitHub\OGSR_Game_Editor\windows\phrase_properties.py'
with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_method = [
    '    @staticmethod\n',
    '    def _validate_syntax(text):\n',
    '        stripped = text.strip()\n',
    '\n',
    '        if stripped != text:\n',
    '            return False\n',
    '\n',
    '        if "(" in stripped:\n',
    '            if not stripped.endswith(")"):\n',
    '                return False\n',
    '\n',
    '            paren_index = stripped.index("(")\n',
    '            func_name_part = stripped[:paren_index]\n',
    '            func_name = func_name_part.strip()\n',
    '\n',
    '            if func_name_part != func_name:\n',
    '                return False\n',
    '\n',
    '            if " " in func_name:\n',
    '                return False\n',
    '\n',
    '            args_str = stripped[paren_index + 1:-1]\n',
    '\n',
    '            if not func_name:\n',
    '                return False\n',
    '\n',
    '            if args_str.strip():\n',
    '                args = [args_str]\n',
    '                in_string = False\n',
    '                string_char = None\n',
    '                result = []\n',
    '                for char in args_str:\n',
    '                    if char in (\'"\', "\'") and not in_string:\n',
    '                        in_string = True\n',
    '                        string_char = char\n',
    '                        result.append(char)\n',
    '                    elif char == string_char and in_string:\n',
    '                        in_string = False\n',
    '                        string_char = None\n',
    '                        result.append(char)\n',
    '                    elif char == \',\' and not in_string:\n',
    "                        result.append('\\x00')\n",
    '                    else:\n',
    '                        result.append(char)\n',
    "                split_args = ''.join(result).split('\\x00')\n",
    '\n',
    '                for arg in split_args:\n',
    '                    arg = arg.strip()\n',
    '                    if not arg:\n',
    '                        return False\n',
    "                    if not (arg.startswith(\"'\") and arg.endswith(\"'\") and len(arg) > 2):\n",
    '                        return False\n',
    "                    inner = arg[1:-1]\n",
    '                    if \'"\' in inner:\n',
    '                        return False\n',
    "                    if \"'\" in inner:\n",
    '                        return False\n',
    '\n',
    '                return True\n',
    '            else:\n',
    '                return False\n',
    '        else:\n',
    '            return True\n',
    '\n',
]

# Find the method
start_idx = None
end_idx = None
for i, line in enumerate(lines):
    if line.strip() == 'def _validate_syntax(text):':
        start_idx = i - 1
    if start_idx is not None and end_idx is None:
        if i > start_idx + 2:
            stripped = line.lstrip()
            if stripped and not stripped.startswith('#') and not stripped.startswith('def _validate'):
                indent = len(line) - len(stripped)
                if indent <= 4:
                    end_idx = i
                    break

if end_idx is None:
    end_idx = len(lines)

print(f"Replacing lines {start_idx+1}-{end_idx}")
lines[start_idx:end_idx] = new_method

with open(filepath, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('OK')
