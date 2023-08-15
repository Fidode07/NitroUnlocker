from colorama import Fore


def out(t: str, d: str) -> None:
    print(f'{Fore.CYAN}{t}: {Fore.GREEN}{d}')
