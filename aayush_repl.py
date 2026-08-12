#!/usr/bin/env python3
import atexit
import code
import os
import readline
import rlcompleter
import sys

VERSION = '3.1.0'
RED = '\033[1;31m'
BLUE = '\033[38;2;77;93;250m'   # #4d5dfa
WHITE = '\033[1;37m'
GRAY = '\033[0;90m'
GREEN = '\033[1;32m'
YELLOW = '\033[1;33m'
RESET = '\033[0m'

HISTORY_FILE = os.path.expanduser('~/.aayush_repl_history')
EXIT_WORDS = ('exit', 'quit', 'exit()', 'quit()')

BANNER = f'''{BLUE}
██████╗ ███████╗██████╗ ██╗
██╔══██╗██╔════╝██╔══██╗██║
██████╔╝█████╗  ██████╔╝██║
██╔══██╗██╔══╝  ██╔═══╝ ██║
██║  ██║███████╗██║     ██║
╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝
{RED}                         BY AAYUSH
{GRAY}                    Python REPL for Termux
{RESET}'''

HELP = f'''{BLUE}AAYUSH REPL — COMMANDS{RESET}

  {RED}help{RESET}       Show this command list
  {RED}banner{RESET}     Show the AAYUSH REPL banner
  {RED}clear{RESET}      Clear the terminal (alias: cls)
  {RED}about{RESET}      Show project information
  {RED}version{RESET}    Show version
  {RED}python{RESET}     Show Python version
  {RED}history{RESET}    Show recent REPL history
  {RED}exit{RESET}       Exit Aayush REPL
  {RED}quit{RESET}       Exit Aayush REPL

{GRAY}Everything else is evaluated by the real Python interpreter.
Multiline Python, functions, classes, imports, exceptions, etc. work normally.
Tab-completion and cross-session history are enabled.{RESET}
'''


def clear():
    os.system('clear')


def show_banner():
    print(BANNER)


def cmd_about():
    print(f'\n{BLUE}Aayush REPL{RESET} v{VERSION}\nCreated by Aayush for Termux.\n')


def cmd_version():
    print(f'Aayush REPL v{VERSION}')


def cmd_python():
    print(sys.version)


def show_history():
    try:
        n = readline.get_current_history_length()
        if n == 0:
            print(f'{GRAY}No history yet.{RESET}')
            return
        start = max(1, n - 19)
        for i in range(start, n + 1):
            item = readline.get_history_item(i)
            if item:
                print(f'{GRAY}{i:>4}{RESET}  {item}')
    except Exception:
        print(f'{GRAY}History is unavailable in this environment.{RESET}')


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
    'help': lambda: print(HELP),
    'banner': show_banner,
    'clear': clear,
    'cls': clear,
    'about': cmd_about,
    'version': cmd_version,
    'python': cmd_python,
    'history': show_history,
}


class AayushConsole(code.InteractiveConsole):
    def raw_input(self, prompt=''):
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
        if 'libedit' in (readline.__doc__ or ''):
            readline.parse_and_bind('bind ^I rl_complete')
        else:
            readline.parse_and_bind('tab: complete')
        readline.set_completer_delims(readline.get_completer_delims().replace("'", '').replace('"', ''))
    except Exception:
        pass


def next_indent(line):
    """Work out the indentation the *next* continuation line should start with."""
    stripped = line.rstrip()
    leading = len(line) - len(line.lstrip(' '))
    base = ' ' * leading
    if stripped.endswith(':'):
        return base + '    '
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
    print(f'{GREEN}Type {RED}help{GREEN} for Aayush REPL commands.{RESET}\n')

    load_history()
    atexit.register(save_history)

    console = AayushConsole()
    setup_completion(console)

    while True:
        readline.set_pre_input_hook(None)
        try:
            line = input(f'{RED}>>> {RESET}')
        except KeyboardInterrupt:
            print()
            print(f'{RED}KeyboardInterrupt{RESET}')
            continue
        except EOFError:
            print()
            break

        stripped = line.strip()
        cmd = stripped.lower()

        if cmd == '':
            continue

        # Bare command words only fire when the user hasn't shadowed them
        # with a real variable/function of the same name.
        if cmd in EXIT_WORDS and stripped not in console.locals:
            print(f'{GREEN}Goodbye! 👋{RESET}')
            break

        if cmd in COMMANDS and stripped not in console.locals:
            COMMANDS[cmd]()
            continue

        # Feed normal input into the real Python InteractiveConsole.
        # InteractiveConsole preserves Python's multiline behavior.
        more = console.push(line)
        indent = next_indent(line) if more else ''
        while more:
            readline.set_pre_input_hook(make_indent_hook(indent))
            try:
                cont = input(f'{YELLOW}... {RESET}')
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
            indent = next_indent(cont) if more else ''

    save_history()


if __name__ == '__main__':
    main()
