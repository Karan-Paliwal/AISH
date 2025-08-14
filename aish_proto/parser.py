import json
from thefuzz import process

def load_patterns():
    with open("patterns.json") as f:
        return json.load(f)

def find_command(user_input):
    patterns = load_patterns()
    best_match = process.extractOne(user_input, patterns.keys())
    if best_match and best_match[1] >= 70:
        return patterns[best_match[0]]
    return None
