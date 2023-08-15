from ext.discord_helper import DiscordHelper
from ext.out import out
from colorama import Fore
import os

# Fix some weird color problems: https://stackoverflow.com/questions/64159164/cmd-color-problems
os.system("")


class StringHelper:
    def __init__(self, width: int, title: str) -> None:
        if width % 2 != 0:
            raise AttributeError('Please make sure the width is 2, 4, 6, ...')

        self.__copyright: str = 'Nitro Unlocker by Fido_de07'
        if width <= len(title) or width <= len(self.__copyright):
            raise AttributeError(
                f'Please make sure that the width is bigger then {max([len(title), len(self.__copyright)])}')

        self.__width: int = width
        self.__title: str = title

        self.__half_center_padding: int = ((self.__width - len(self.__title)) // 2)

    def generate_table(self) -> str:
        r: str = Fore.LIGHTGREEN_EX + '-' * self.__width + '\n'
        r += '|' + ' ' * (self.__width - 2) + '|\n'
        r += '|'
        r += ' ' * (self.__half_center_padding - 1) + Fore.RED + self.__title + Fore.LIGHTGREEN_EX + ' ' * (
                self.__half_center_padding - 1)
        r += '|\n'
        r += '|' + ' ' * (self.__width - 2) + '|\n'
        r += '|' + ' ' * (self.__width - (
                len(self.__copyright) + 4)) + Fore.RED + self.__copyright + Fore.LIGHTGREEN_EX + ' ' * 2 + '|\n'
        r += '-' * self.__width
        return r


def main() -> None:
    str_helper: StringHelper = StringHelper(title='Nitro Unlocker', width=80)
    print(str_helper.generate_table())

    dc_helper: DiscordHelper = DiscordHelper()

    dc_path: str = dc_helper.get_discord_path()
    out('Discord Path', dc_path)
    out('Attempt 1', 'Try to extract core.asar ...')
    print('\nActions:')
    out('[0]', 'Unlock Nitro')
    out('[1]', 'Restore Backup')
    out('->', 'Any other key to exit')
    print(Fore.RED)
    action: str = input('_> ').strip()
    if not any([action == '0', action == '1']):
        return
    if action == '0':
        dc_helper.kill_discord_procs()
        dc_helper.extract_core_asar()  # extracts core.asar
        dc_helper.inject_nitro_unlocker()
        dc_helper.compress_asar()
        dc_helper.clear()  # deletes the tmp directory
        return
    # action is 1
    dc_helper.restore_backup()

    # Reset Color
    print(Fore.RESET)


if __name__ == '__main__':
    main()
