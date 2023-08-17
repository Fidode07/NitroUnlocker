from typing import *

from ext.process_helper import ProcessHelper, Window

proc_helper: ProcessHelper = ProcessHelper()
discord_queries: List[Window] = proc_helper.find_window_by_title('discord', only_contains=True)
discord = discord_queries[0]
print(discord_queries)
print(discord)
print('Path', proc_helper.get_exec_path_by_hwnd(discord.hwnd))
# print('Kill Discord Proc ...')
# proc_helper.kill_proc_by_hwnd(discord.hwnd)
