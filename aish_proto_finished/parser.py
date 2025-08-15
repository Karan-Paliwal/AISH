# parser.py
import json
import re
from difflib import get_close_matches
from typing import Optional, Tuple, List
from utils import resource_path
from core_commands import COMMAND_REGISTRY

def normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip())

def load_json(path: str):
    with open(resource_path(path), 'r', encoding='utf-8') as f:
        return json.load(f)

# parser returns either:
#  - ("builtin", func, args:list)
#  - ("shell", command_string)
#  - None
def parse_command(user_input: str, commands_json: dict, patterns_json: dict, current_os: str):
    ui = normalize(user_input)
    if ui == "":
        return None

    # 1. Patterns: exact match
    if ui in patterns_json:
        key = patterns_json[ui]
        # If pattern maps to builtin
        if key in COMMAND_REGISTRY:
            return ("builtin", COMMAND_REGISTRY[key], [])
        # If pattern maps to shell command key
        if key in commands_json:
            cmd = commands_json[key].get(current_os, commands_json[key].get("linux"))
            return ("shell", cmd)

    # 2. If the exact first token matches a builtin or command key or pattern
    parts = ui.split()
    head = parts[0]
    tail = parts[1:]

    # builtin exact
    if head in COMMAND_REGISTRY:
        return ("builtin", COMMAND_REGISTRY[head], tail)

    # pattern head exact
    if head in patterns_json:
        mapped = patterns_json[head]
        if mapped in COMMAND_REGISTRY:
            return ("builtin", COMMAND_REGISTRY[mapped], tail)
        if mapped in commands_json:
            cmd = commands_json[mapped].get(current_os, commands_json[mapped].get("linux"))
            full = f"{cmd} {' '.join(tail)}".strip()
            return ("shell", full)

    # commands.json exact
    if head in commands_json:
        base = commands_json[head].get(current_os, commands_json[head].get("linux"))
        full = f"{base} {' '.join(tail)}".strip()
        return ("shell", full)

    # 3. fuzzy match for patterns then commands
    cand = get_close_matches(ui, patterns_json.keys(), n=1, cutoff=0.8)
    if cand:
        key = patterns_json[cand[0]]
        if key in COMMAND_REGISTRY:
            return ("builtin", COMMAND_REGISTRY[key], [])
        if key in commands_json:
            cmd = commands_json[key].get(current_os, commands_json[key].get("linux"))
            return ("shell", cmd)

    cand_cmd = get_close_matches(head, commands_json.keys(), n=1, cutoff=0.8)
    if cand_cmd:
        base = commands_json[cand_cmd[0]].get(current_os, commands_json[cand_cmd[0]].get("linux"))
        full = f"{base} {' '.join(tail)}".strip()
        return ("shell", full)

    # 4. last-ditch: treat whole input as shell passthrough
    return ("shell", ui)
