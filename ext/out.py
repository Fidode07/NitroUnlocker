from dataclasses import dataclass
import os

# Fix some weird color problems: https://stackoverflow.com/questions/64159164/cmd-color-problems
os.system('')


@dataclass
class Color:
    main: str = '\u001b'
    black: str = f'{main}[30m'
    red: str = f'{main}[31m'
    green: str = f'{main}[32m'
    yellow: str = f'{main}[33m'
    blue: str = f'{main}[34m'
    magenta: str = f'{main}[35m'
    cyan: str = f'{main}[36m'
    white: str = f'{main}[37m'

    bright_black: str = black[:-1] + ';1m'
    bright_red: str = red[:-1] + ';1m'
    bright_green: str = green[:-1] + ';1m'
    bright_yellow: str = yellow[:-1] + ';1m'
    bright_blue: str = blue[:-1] + ';1m'
    bright_magenta: str = magenta[:-1] + ';1m'
    bright_cyan: str = cyan[:-1] + ';1m'
    bright_white: str = white[:-1] + ';1m'

    bold: str = f'{main}[1m'
    underline: str = f'{main}[4m'
    reversed: str = f'{main}[7m'

    reset: str = f'{main}[0m'


def out(t: str, d: str) -> None:
    print(f'{Color.bright_cyan}{t}: {Color.green}{d}')
