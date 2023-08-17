import os
import shutil
from subprocess import Popen, DEVNULL
from typing import *

from ext.asar_helper import AsarHelper
from ext.out import out
from ext.process_helper import Window, ProcessHelper


class ExtractionError(Exception):
    pass


class NoEntryPoint(Exception):
    pass


class PackingError(Exception):
    pass


class DiscordHelper:
    def __init__(self) -> None:
        self.__proc_helper: ProcessHelper = ProcessHelper()
        self.__dc_proc: Union[Window, None] = None

    def kill_discord_procs(self) -> None:
        if self.__dc_proc:
            self.__proc_helper.kill_proc_by_hwnd(self.__dc_proc.hwnd, timeout=1.5)
            return
        self.__init_dc_proc()
        self.kill_discord_procs()

    def __init_dc_proc(self) -> None:
        if self.__dc_proc:
            return
        results: List[Window] = self.__proc_helper.find_window_by_title('discord')
        length: int = len(results)
        if length == 0:
            raise ProcessLookupError('Please start discord before using this tool!')
        if length > 1:
            results = [x for x in results if x.executable_path.endswith('Discord.exe')]
            if len(results) == 1:
                self.__dc_proc = results[0]
                return
            raise ChildProcessError('Sorry, found multiple discord procs.')
        self.__dc_proc = results[0]

    def get_discord_path(self) -> str:
        if self.__dc_proc:
            return self.__dc_proc.executable_path
        self.__init_dc_proc()
        return self.get_discord_path()

    def get_static_discord_path(self) -> str:
        """
        :return: something similar like C:/Users/Fido_de07/AppData/Local/Discord/app-1.0.9016
        """
        return '/'.join(self.get_discord_path().split('\\')[:-1])

    def extract_core_asar(self) -> None:
        os.makedirs('tmp', exist_ok=True)
        if len(os.listdir('tmp')) > 0:
            raise FileExistsError('Please make sure that the tmp folder is empty or deleted!')
        os.makedirs('backup', exist_ok=True)
        if len(os.listdir('backup')) > 0:
            if os.path.isfile('backup/package.json'):
                out('Attempt 1', 'Found valid backup, use old asar instead')
                self.__copy_folder('backup', 'tmp')
                return
            raise FileExistsError(
                'Invalid backup structure! Please make sure that the backup folder is empty or deleted!')

        # p: Popen = Popen(f'cd {os.getcwd()} & npx asar extract {self.__get_core_asar_path()} tmp & exit', shell=True)
        # p.wait()
        # if len(os.listdir('tmp')) == 0 or not os.path.isfile('tmp/package.json'):
        #     raise ExtractionError('Unable to extract core.asar, make sure Node is installed!')

        AsarHelper.extract_asar(self.__get_core_asar_path(), 'tmp')

        out('Attempt 1', 'Extracted Core.asar')
        out('Attempt 1', 'Create Backup of current core.asar ...')
        shutil.move(self.__get_core_asar_path(), 'backup/old-core.asar')
        self.__copy_folder('tmp', 'backup')
        out('Attempt 1', 'Finish')

    def __copy_folder(self, src_folder: str, dst_folder: str) -> None:
        os.makedirs(src_folder, exist_ok=True)
        os.makedirs(dst_folder, exist_ok=True)

        p: Popen = Popen(f'xcopy /E {src_folder} {dst_folder}', stdout=DEVNULL, stderr=DEVNULL, shell=False)
        p.wait()

    def __get_core_asar_path(self, check_exists: bool = True) -> str:
        core_asar_path: str = self.get_static_discord_path() + \
                              '/modules/discord_desktop_core-1/discord_desktop_core/core.asar'
        if all([not os.path.isfile(core_asar_path), check_exists]):
            print(core_asar_path)
            raise FileNotFoundError('Unable to find core.asar!')
        return core_asar_path

    def clear(self) -> None:
        def delete_tree(files: list, top_dir: str) -> None:
            for file in files:
                full_path = os.path.join(top_dir, file)
                if os.path.isfile(full_path):
                    os.remove(full_path)
                else:
                    # It's a directory
                    delete_tree(os.listdir(full_path), full_path)
            os.rmdir(top_dir)

        delete_tree(os.listdir('tmp'), 'tmp')

    def inject_nitro_unlocker(self) -> None:
        out('Attempt 2', 'Try reading mainScreen.js ...')
        target1: str = 'tmp/app/mainScreen.js'
        with open(target1, 'r') as f:
            file_content: str = f.read()
        entry_point: int = file_content.index('mainWindow.on(\'blur\'')

        if entry_point == -1:
            raise NoEntryPoint('Unable to find entry point!')

        out('Attempt 2', f'Found entry point {entry_point}, start injecting ...')

        with open(target1, 'w') as f:
            f.write(file_content[:entry_point] + '''
             mainWindow.webContents.on('dom-ready', function () {
                    mainWindow.webContents.executeJavaScript(`
                        class NitroUnlocker {
    static getNonEmptyExportsFromModuleCache() {
        const moduleCache = wpRequire.c;
        const nonEmptyExports = Object.keys(moduleCache)
            .map(moduleKey => moduleCache[moduleKey].exports) // Get exports for each module key
            .filter(exports => exports !== undefined); // Filter out undefined exports
        return nonEmptyExports;
    }

    static findMatchingExport(expression) {
        const exports = NitroUnlocker.getNonEmptyExportsFromModuleCache();

        for (const moduleExports of exports) {
            if (moduleExports.default && expression(moduleExports.default)) return moduleExports.default;
            if (moduleExports.Z && expression(moduleExports.Z)) return moduleExports.Z;
            if (expression(moduleExports)) return moduleExports;
        }
    }

    static checkPropsExist(...props) {
        // check if props are def. in an target 
        const arePropsDefined = target => props.every((prop => target[prop] !== undefined));
        return NitroUnlocker.findMatchingExport(arePropsDefined);
    }

    static loader() {
        window.webpackChunkdiscord_app.push([
            [Math.random()], {},
            e => {
                window.wpRequire = e
            }
        ]);
        let user = NitroUnlocker.checkPropsExist('getCurrentUser').getCurrentUser();
        if (!user) return; // can't find user
        clearInterval(z) // clear z interval and overwrite it with own 
        user.premiumType = 2; // update user to new nitro tier
    }
}

z = setInterval(NitroUnlocker.loader, 100);
                    `);
                });
            ''' + file_content[entry_point:])
        del file_content
        out('Attempt 2', 'Editing finished')

    def __pack_asar(self, src_folder: str) -> None:
        # p: Popen = Popen(f'npx asar pack {src_folder} new-core.asar', shell=True)
        # p.wait()
        # i: int = 0
        # exists: bool = os.path.isfile('new-core.asar')
        # while not exists:
        #     if i > 9:
        #         raise PackingError('Unable to pack new-core.asar')
        #     time.sleep(1)
        #     exists = os.path.isfile('new-core.asar')
        #     i += 1
        AsarHelper.pack_asar(src_folder, 'new-core.asar')

    def compress_asar(self) -> None:
        out('Attempt 3', 'Pack Folder into new-core.asar ...')

        self.__pack_asar('tmp')

        out('Attempt 3', 'Successfully, kill discord process and move files.')
        if os.path.isfile(self.__get_core_asar_path(check_exists=False)):
            os.remove(self.__get_core_asar_path())
        shutil.move('new-core.asar', self.__get_core_asar_path(check_exists=False))
        out('Attempt 3', 'Packaging finished, restart discord.')
        # Popen(self.get_discord_path(), shell=True)

    def restore_backup(self) -> None:
        if not all([os.path.isdir('backup') and os.path.isfile('backup/package.json')]):
            raise FileNotFoundError('Sorry, there is no backup.')
        self.kill_discord_procs()  # Important, otherwise .asar is used by other procs

        if os.path.isfile('backup/old-core.asar'):
            if os.path.isfile(self.__get_core_asar_path(check_exists=False)):
                os.remove(self.__get_core_asar_path())
            shutil.copy('backup/old-core.asar', self.__get_core_asar_path(check_exists=False))
            return

        # Backup dir exists, old-core.asar wasn't created yet
        if all([os.path.isfile('backup/package.json'), os.path.isdir('backup/app')]):
            self.__pack_asar('backup')
            if os.path.isfile(self.__get_core_asar_path(check_exists=False)):
                os.remove(self.__get_core_asar_path())
            shutil.move('new-core.asar', self.__get_core_asar_path(check_exists=False))
            return
        raise FileNotFoundError('Sorry, there is no backup.')
