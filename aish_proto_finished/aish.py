#!/usr/bin/env python3
# aish.py
"""
AISH — integrated main program (UI/UX from animations.py + built-in useful commands).
Keeps the menu-driven UI and animations, but will run builtin functions from core_commands
or fall back to shell commands resolved via commands.json (OS-aware).
"""

import os
import json
import subprocess
import time
import random
from typing import Dict, Any, List

from colorama import Fore, Style, init

# import animations (from the files your friend provided)
from animations import display_banner, glitch_animation, impact_animation

# local helpers & commands
from utils import resource_path, detect_os, run_subprocess
import core_commands

# initialize colorama
init(autoreset=True)

# Load commands + patterns
def load_json_safe(fname: str) -> Dict[str, Any]:
    try:
        path = resource_path(fname)
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

commands_json = load_json_safe("commands.json")
patterns_json = load_json_safe("patterns.json")

HISTORY_FILE = resource_path("history.json") if True else "history.json"  # resource_path returns base path
OS_NAME = detect_os()

# ----------------------------
# Small local animation wrappers (keeps UI/UX consistent)
# ----------------------------
def start_animation(duration: float = 1.0):
    spinner = ["|", "/", "-", "\\"]
    end = time.time() + duration
    msg = Fore.GREEN + "Launching AISH" + Style.RESET_ALL + " "
    while time.time() < end:
        for s in spinner:
            print("\r" + msg + s, end="", flush=True)
            time.sleep(0.06)
            if time.time() >= end:
                break
    print("\r" + " " * (len(msg) + 2) + "\r", end="", flush=True)

def processing_animation(duration: float = 0.9):
    spinner = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    end = time.time() + duration
    while time.time() < end:
        for s in spinner:
            print("\r" + Fore.YELLOW + "Processing " + s + Style.RESET_ALL, end="", flush=True)
            time.sleep(0.06)
            if time.time() >= end:
                break
    print("\r" + " " * 40 + "\r", end="", flush=True)

def success_animation():
    symbols = ["*", "+", "·", "•"]
    cols = [Fore.GREEN, Fore.LIGHTGREEN_EX]
    for _ in range(4):
        row = "".join(random.choice(cols) + random.choice(symbols) for _ in range(24))
        print(row + Style.RESET_ALL)
        time.sleep(0.02)
    print(Fore.GREEN + "✔ Success!" + Style.RESET_ALL)

def blast_animation():
    try:
        impact_animation()
    except Exception:
        try:
            glitch_animation("ERROR", repeat=3, delay=0.06)
        except Exception:
            pass
        print(Fore.RED + "Invalid input." + Style.RESET_ALL)

def exit_animation():
    msg = Fore.MAGENTA + "Goodbye." + Style.RESET_ALL
    for i in range(3):
        print("\r" + msg + "." * i, end="", flush=True)
        time.sleep(0.25)
    print("\r" + " " * (len(msg) + 3) + "\r", end="", flush=True)

# ----------------------------
# history helpers
# ----------------------------
def append_history(entry: str):
    try:
        path = resource_path("history.json")
        # if resource_path returned a temp _MEIPASS path when packaged, write history next to exe instead
        if hasattr(__import__("sys"), "_MEIPASS"):
            # packaged: write to user folder instead
            path = os.path.join(os.path.expanduser("~"), ".aish_history.json")
        hist = []
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    hist = json.load(f) or []
            except Exception:
                hist = []
        hist.append({"time": time.strftime("%Y-%m-%d %H:%M:%S"), "entry": entry})
        with open(path, "w", encoding="utf-8") as f:
            json.dump(hist, f, indent=2)
    except Exception:
        # silent fail (history is convenience)
        pass

# ----------------------------
# grouped commands (UI browsing)
# ----------------------------
def grouped_commands(cmds: Dict[str, Any]) -> Dict[str, List]:
    groups = {
        "File Operations": [],
        "Development": [],
        "System": [],
        "Utilities": [],
        "Other": []
    }
    for name, desc in cmds.items():
        desc_str = ""
        if isinstance(desc, dict):
            desc_str = desc.get("description", "")
        else:
            desc_str = str(desc)
        lower_name = name.lower()
        if any(t in lower_name for t in ("ls", "cd", "mkdir", "rm", "touch", "mv", "zip", "unzip")) or "file" in desc_str.lower():
            groups["File Operations"].append((name, desc_str))
        elif any(t in lower_name for t in ("python", "node", "git", "make")):
            groups["Development"].append((name, desc_str))
        elif any(t in lower_name for t in ("top", "htop", "df", "free", "ps", "sysinfo", "battery")):
            groups["System"].append((name, desc_str))
        elif any(t in lower_name for t in ("curl", "wget", "ping", "scp", "scanport", "traceroute")):
            groups["Utilities"].append((name, desc_str))
        else:
            groups["Other"].append((name, desc_str))
    return groups

# ----------------------------
# decision: builtin or shell passthrough
# ----------------------------
def resolve_and_run(raw_input: str):
    s = raw_input.strip()
    if not s:
        blast_animation()
        return

    # quick pattern match (exact)
    key = None
    lowered = s.lower()
    if lowered in patterns_json:
        key = patterns_json[lowered]

    # if a pattern maps to a builtin command name present in core_commands registry
    if key and key in core_commands.COMMAND_REGISTRY:
        func = core_commands.COMMAND_REGISTRY[key]
        try:
            processing_animation()
            # split remainder args if any (we used exact pattern; no extra args here)
            func([])
            success_animation()
            append_history(s)
            return
        except Exception:
            blast_animation()
            return

    # direct builtin (first token)
    tokens = s.split()
    head = tokens[0].lower()
    tail = tokens[1:]
    if head in core_commands.COMMAND_REGISTRY:
        func = core_commands.COMMAND_REGISTRY[head]
        try:
            processing_animation()
            func(tail)
            success_animation()
            append_history(s)
            return
        except Exception:
            blast_animation()
            return

    # if head matches commands.json keys (shell mapping), build os-aware command
    if head in commands_json:
        entry = commands_json[head]
        cmd_template = entry.get(OS_NAME) if isinstance(entry, dict) else entry
        if not cmd_template and isinstance(entry, dict):
            # fallback to linux
            cmd_template = entry.get("linux") or ""
        # append tail as arguments
        cmd_to_run = f"{cmd_template} {' '.join(tail)}".strip()
        try:
            processing_animation()
            run_shell_command(cmd_to_run)
            success_animation()
            append_history(s)
            return
        except Exception:
            blast_animation()
            return

    # fallback: treat entire input as shell passthrough
    try:
        processing_animation()
        run_shell_command(s)
        success_animation()
        append_history(s)
    except Exception:
        blast_animation()

def run_shell_command(cmd: str):
    """
    Runs an arbitrary shell command (shell=True) using subprocess.run and prints output.
    We run it in the current terminal so user sees stdout/stderr directly.
    """
    # handle clear specially to keep cross-platform behavior
    low = cmd.strip().lower()
    if low in ("clear", "cls"):
        os.system("cls" if OS_NAME == "windows" else "clear")
        return
    # run and stream output
    try:
        proc = subprocess.run(cmd, shell=True)
        return proc.returncode
    except Exception as e:
        raise

# ----------------------------
# Menu loop
# ----------------------------
def main():
    # show banner and small start animation
    try:
        display_banner()
    except Exception:
        # fallback banner
        print(Fore.CYAN + "AISH" + Style.RESET_ALL)
        print(Fore.CYAN + "By AIRZ01" + Style.RESET_ALL)
    start_animation()

    while True:
        print(Fore.CYAN + Style.BRIGHT + "\n=== AISH – Menu Interface ===" + Style.RESET_ALL)
        print(Fore.YELLOW + "1)" + Style.RESET_ALL + " Run a command (natural language or direct)")
        print(Fore.YELLOW + "2)" + Style.RESET_ALL + " Browse commands (grouped)")
        print(Fore.YELLOW + "3)" + Style.RESET_ALL + " Show history")
        print(Fore.YELLOW + "4)" + Style.RESET_ALL + " Utilities (list builtins)")
        print(Fore.YELLOW + "5)" + Style.RESET_ALL + " Safety check (if available)")
        print(Fore.YELLOW + "6)" + Style.RESET_ALL + " Exit")

        choice = input(Fore.GREEN + "Choose an option: " + Style.RESET_ALL).strip()

        if choice == "1":
            user_cmd = input("\nEnter command (NL or shell): ").strip()
            if not user_cmd:
                blast_animation()
                continue
            resolve_and_run(user_cmd)

        elif choice == "2":
            groups = grouped_commands(commands_json)
            for group, cmds in groups.items():
                print(Fore.MAGENTA + f"\n{group}:" + Style.RESET_ALL)
                for cmd, desc in cmds:
                    print(Fore.CYAN + f"  {cmd}" + Style.RESET_ALL + (f" – {desc}" if desc else ""))

        elif choice == "3":
            history_file = resource_path("history.json")
            altpath = os.path.join(os.path.expanduser("~"), ".aish_history.json")
            usepath = altpath if (os.path.exists(altpath) and not os.path.exists(history_file)) else history_file
            if os.path.exists(usepath):
                try:
                    with open(usepath, "r", encoding="utf-8") as hf:
                        hist = json.load(hf)
                    if not hist:
                        print(Fore.YELLOW + "No history yet." + Style.RESET_ALL)
                    else:
                        print("\nLast entries (most recent first):")
                        for i, h in enumerate(reversed(hist[-50:]), 1):
                            t = h.get("time", "")
                            e = h.get("entry", "")
                            print(f"{i}) {t} — {e}")
                except Exception:
                    print(Fore.RED + "Failed to read history." + Style.RESET_ALL)
            else:
                print(Fore.YELLOW + "History not available." + Style.RESET_ALL)

        elif choice == "4":
            # List builtins available via core_commands
            print(Fore.MAGENTA + "\nBuilt-in utilities (AISH):" + Style.RESET_ALL)
            for k in sorted(core_commands.COMMAND_REGISTRY.keys()):
                print(Fore.CYAN + f"  {k}" + Style.RESET_ALL + f" – {core_commands.COMMAND_REGISTRY[k].__doc__ or ''}")

        elif choice == "5":
            try:
                import safety as s
                if hasattr(s, "check"):
                    target = input("Enter command to safety-check: ").strip()
                    res = s.check(target)
                    print("Safety result:", res)
                else:
                    print("No safety check function found in safety.py")
            except Exception:
                print("Safety module not available or failed to run.")

        elif choice == "6":
            exit_animation()
            break
        else:
            blast_animation()

if __name__ == "__main__":
    main()
