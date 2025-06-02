# https://cdn.jsdelivr.net/npm/micro-repl@0.5.2/serial.js

from pyscript import window, document
from pyscript.js_modules.micro_repl import default as Board
import json, asyncio

FIFO_SIZE = 10000

list_code = '''
import os
def listdir(directory):
    result = set()
    def _listdir(dir_or_file):
        try:
            children = os.listdir(dir_or_file)
        except OSError:
            os.stat(dir_or_file)
            result.add(dir_or_file)
        else:
            if children:
                for child in children:
                    if dir_or_file == '/':
                        next = dir_or_file + child
                    else:
                        next = dir_or_file + '/' + child
                    _listdir(next)
            else:
                result.add(dir_or_file)
    _listdir(directory)
    return sorted(result)

listdir('/')
'''

try:
    window.navigator.serial.requestPort
except:
    window.alert('you have to use Chrome to talk over serial')

class uRepl():
    def __init__(self, baudrate = 115200, buffer_size = 256):
        self.connected = False
        self.terminal = None
        self.disconnect_callback = None
        self.newData_callback = None
        self.buffer = ''
        self.buffer_size = buffer_size
        #self.update(0)
        self.path = None
        self.board = Board({
            "baudRate": baudrate,
            "dataType": "string",
            "onconnect": self.on_connect,
            "ondisconnect": self.on_disconnect,
            "ondata": self.on_data,
            "onresult": json.loads,
            "onerror": window.alert,
            "fontSize": '24',
            "fontFamily": 'Courier New',
            "theme": {
                "background": "white",
                "foreground": "black",
            },
        })

    def on_data(self, chunk):
        self.buffer += chunk
        self.buffer = self.buffer[-FIFO_SIZE:]
        if self.newData_callback: self.newData_callback(chunk)
    
    def on_connect(self):
        window.console.log('connected')
        self.connected = True
        self.terminal = self.board.terminal

    async def on_disconnect(self):
        self.connected = False
        #self.terminal.reset()
        self.terminal = None
        if self.disconnect_callback:  
            await self.disconnect_callback()

    async def on_reset(self, error):
        self.reset.disabled = True
        await self.board.reset()
        self.reset.disabled = False

    async def eval(self,payload, hidden=False):
        return await self.board.eval(payload, hidden=hidden)

    async def paste(self,payload, hidden=False):
        return await self.board.paste(payload, hidden=hidden)

    def focus(self):
        self.terminal.focus()

    async def getList(self, list_files = None, desired = "hubname"):
        info = None
        if self.connected:
            window.console.log('getting file listing')
            array = await self.eval(list_code, hidden = True)
            if list_files:
                list_files.options.length = 0
                if array:
                    for name in array:
                        if name.find('/.') == 0:# not '.py' in name or name.find('/.') == 0:
                            continue
                        if desired in name:
                            info = name
                        option = document.createElement('option')
                        option.text = name
                        option.value = name
                        list_files.add(option)
        return info
