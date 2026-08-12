#!/usr/bin/env python3
# aayush_repl.py
#
# Custom REPL wrapper for Termux. Basically stdlib `code.InteractiveConsole`
# with some quality-of-life stuff bolted on - colors, history across
# sessions, a few shortcut commands, and auto-indent for multiline blocks
# (readline doesn't do this by default and it drove me crazy).
#
# - Aayush

import atexit
import code
import os
import readline
import rlcompleter
import sys

VERSION = "3.1.0"

# ANSI colors. Not bothering with a colors lib for something this small.
RED = "\033[1;31m"
BLUE = "\033[38;2;77;93;250m"  # brandish blue, #4d5dfa
WHITE = "\033[1;37m"
GRAY = "\033[0;90m"
GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
RESET = "\033[0m"

HISTORY_FILE = os.path.expanduser("~/.aayush_repl_history")
EXIT_WORDS = ("exit", "quit", "exit()", "quit()")

BANNER = f"""{BLUE}
██████╗ ███████╗██████╗ ██╗
██╔══██╗██╔════╝██╔══██╗██║
██████╔╝█████╗  ██████╔╝██║
██╔══██╗██╔══╝  ██╔═══╝ ██║
██║  ██║███████╗██║     ██║
╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝
{RED}                         BY AAYUSH
{GRAY}                    Python REPL for Termux
{RESET}"""

HELP = f"""{BLUE}AAYUSH REPL — COMMANDS{RESET}

  {RED}help{RESET}       Show this command list
  {RED}banner{RESET}     Show the AAYUSH REPL banner
  {RED}clear{RESET}      Clear the terminal (alias: cls)
  {RED}about{RESET}      Show project info
  {RED}version{RESET}    Show version
  {RED}python{RESET}     Show Python version
  {RED}history{RESET}    Show recent REPL history
  {RED}exit{RESET}       Exit Aayush REPL
  {RED}quit{RESET}       Exit Aayush REPL

{GRAY}Everything else just gets handed off to the real Python interpreter.
Multiline blocks, functions, classes, imports, exceptions - all work
like a normal REPL. Tab-completion and cross-session history included.{RESET}
"""


def clear():
    os.system("clear")


def show_banner():
    print(BANNER)


def cmd_about():
    print(f"\n{BLUE}Aayush REPL{RESET} v{VERSION}\nMade by Aayush, for Termux.\n")


def cmd_version():
    print(f"Aayush REPL v{VERSION}")


def cmd_python():
    print(sys.version)


def show_history():
    # readline history is 1-indexed, fun fact
    try:
        n = readline.get_current_history_length()
        if n == 0:
            print(f"{GRAY}No history yet.{RESET}")
            return
        start = max(1, n - 19)  # last 20 entries, no need to dump everything
        for i in range(start, n + 1):
            item = readline.get_history_item(i)
            if item:
                print(f"{GRAY}{i:>4}{RESET}  {item}")
    except Exception:
        # some environments (like certain Termux setups) don't support this
        print(f"{GRAY}History is unavailable in this environment.{RESET}")


def save_history():
    try:
        readline.write_history_file(HISTORY_FILE)
    except OSError:
        pass


def load_history():
    try:
        readline.read_history_file(HISTORY_FILE)
    except (FileNotFoundError, PermissionError, OSError):
        pass
    readline.set_history_length(2000)


COMMANDS = {
    "help": lambda: print(HELP),
    "banner": show_banner,
    "clear": clear,
    "cls": clear,
    "about": cmd_about,
    "version": cmd_version,
    "python": cmd_python,
    "history": show_history,
}


class AayushConsole(code.InteractiveConsole):
    """Same as InteractiveConsole, just with colored errors and input()
    instead of raw_input so it plays nice with readline."""

    def raw_input(self, prompt=""):
        try:
            return input(prompt)
        except EOFError:
            raise SystemExit

    def showtraceback(self):
        sys.stderr.write(RED)
        super().showtraceback()
        sys.stderr.write(RESET)

    def showsyntaxerror(self, filename=None):
        sys.stderr.write(RED)
        super().showsyntaxerror(filename)
        sys.stderr.write(RESET)


def setup_completion(console):
    try:
        readline.set_completer(rlcompleter.Completer(console.locals).complete)
        # macOS ships libedit instead of GNU readline, and it binds tab
        # differently - handle both.
        if "libedit" in (readline.__doc__ or ""):
            readline.parse_and_bind("bind ^I rl_complete")
        else:
            readline.parse_and_bind("tab: complete")
        # let completion work inside quoted strings too
        readline.set_completer_delims(readline.get_completer_delims().replace("'", "").replace('"', ""))
    except Exception:
        # if readline isn't fully there, just skip completion rather than crash
        pass


def next_indent(line):
    """Figure out what indentation the next continuation line should get.
    readline has no idea about Python syntax so we do this ourselves."""
    stripped = line.rstrip()
    leading = len(line) - len(line.lstrip(" "))
    base = " " * leading
    if stripped.endswith(":"):
        return base + "    "
    return base


def make_indent_hook(text):
    def hook():
        if text:
            readline.insert_text(text)
            readline.redisplay()
    return hook


def main():
    clear()
    show_banner()
    print(f"{GREEN}Type {RED}help{GREEN} for Aayush REPL commands.{RESET}\n")

    load_history()
    atexit.register(save_history)

    console = AayushConsole()
    setup_completion(console)

    while True:
        readline.set_pre_input_hook(None)
        try:
            line = input(f"{RED}>>> {RESET}")
        except KeyboardInterrupt:
            print()
            print(f"{RED}KeyboardInterrupt{RESET}")
            continue
        except EOFError:
            print()
            break

        stripped = line.strip()
        cmd = stripped.lower()

        if cmd == "":
            continue

        # Only treat these as commands if the user hasn't shadowed the name
        # with an actual variable/function - e.g. `exit = 5` should still work.
        if cmd in EXIT_WORDS and stripped not in console.locals:
            print(f"{GREEN}Goodbye! 👋{RESET}")
            break

        if cmd in COMMANDS and stripped not in console.locals:
            COMMANDS[cmd]()
            continue

        # Anything else goes straight into the real interpreter.
        # InteractiveConsole.push() handles multiline statements for us.
        more = console.push(line)
        indent = next_indent(line) if more else ""
        while more:
            readline.set_pre_input_hook(make_indent_hook(indent))
            try:
                cont = input(f"{YELLOW}... {RESET}")
            except KeyboardInterrupt:
                print()
                console.resetbuffer()
                more = False
                break
            except EOFError:
                print()
                console.resetbuffer()
                more = False
                break
            finally:
                readline.set_pre_input_hook(None)
            more = console.push(cont)
            indent = next_indent(cont) if more else ""

    save_history()


if __name__ == "__main__":
    main()
