from appdirs import *
import codecs
import json
import asyncio
import socketio
import uuid
import sys

APP_NAME = "electron-spirit"
PLUGIN_NAME = "ES Plugin Example"
SHORT_NAME = "example"
PLUGIN_SETTING = "plugin.setting.json"
DEFAULT_CONFIG = {
    "input_hook": "g",
    "css": ".car { position: relative; width: 100%; height: 100%; padding: 10px; background-color: rgba(250, 250, 250, 1); border: 1px solid black; text-align: center; box-sizing: border-box; overflow: auto; }",
    "basic": "<div class='car'>Hello</div>",
    "basic_bound": {"x": 200, "y": 200, "w": 100, "h": 50},
    "view": "https://www.baidu.com",
    "view_bound": {"x": 300, "y": 300, "w": 300, "h": 300},
}


class PluginApi(socketio.AsyncClientNamespace):
    def __init__(self, parent):
        super().__init__()
        self.elem_count = 0
        self.parent = parent

    def on_connect(self):
        print("Connected")

    def on_disconnect(self):
        print("Disconnected")
        sys.exit(0)

    def on_echo(self, data):
        print("Echo:", data)

    def on_addInputHook(self, data):
        print("Add input hook:", data)

    def on_delInputHook(self, data):
        print("Del input hook:", data)

    def on_insertCSS(self, data):
        print("Insert css:", data)

    def on_removeCSS(self, data):
        print("Remove css:", data)

    def on_addElem(self, data):
        print("Update elem:", data)
        self.elem_count += 1

    def on_delElem(self, data):
        print("Remove elem:", data)
        self.elem_count -= 1

    def on_showElem(self, data):
        print("Show view:", data)

    def on_hideElem(self, data):
        print("Hide view:", data)

    def on_setBound(self, data):
        print("Set bound:", data)

    def on_setContent(self, data):
        print("Set content:", data)

    def on_setOpacity(self, data):
        print("Set opacity:", data)

    def on_execJSInElem(self, data):
        print("Exec js in elem:", data)

    def on_notify(self, data):
        print("Notify:", data)

    def on_updateBound(self, key, bound):
        print("Update bound:", key, bound)
        self.parent.update_bound(key, bound)

    def on_updateOpacity(self, key, opacity):
        print("Update opacity:", key, opacity)

    def on_processContent(self, content):
        print("Process content:", content)

    def on_modeFlag(self, flags):
        print("Mode flag:", flags)

    def on_elemRemove(self, key):
        print("Elem remove:", key)
        return False

    def on_elemRefresh(self, key):
        print("Elem refresh:", key)
        return False


class Plugin(object):
    def __init__(self) -> None:
        self.load_config()
        self.api = PluginApi(self)

    def load_config(self):
        path = user_data_dir(APP_NAME, False, roaming=True)
        with codecs.open(path + "/api.json") as f:
            config = json.load(f)
        self.port = config["apiPort"]
        try:
            with codecs.open(PLUGIN_SETTING) as f:
                self.cfg = json.load(f)
            for k in DEFAULT_CONFIG:
                if k not in self.cfg or type(self.cfg[k]) != type(DEFAULT_CONFIG[k]):
                    self.cfg[k] = DEFAULT_CONFIG[k]
        except:
            self.cfg = DEFAULT_CONFIG
        self.save_cfg()

    def save_cfg(self):
        with codecs.open(PLUGIN_SETTING, "w") as f:
            json.dump(self.cfg, f)

    def update_bound(self, key, _type, bound):
        if key == "ex-1":
            self.cfg["basic_bound"] = bound
        elif key == "ex-2":
            self.cfg["view_bound"] = bound
        self.save_cfg()

    async def wait_for_elem(self):
        while self.api.elem_count < 2:
            await asyncio.sleep(0.1)

    async def test_case(self):
        # get input 'foo' from like '!g foo'
        await sio.emit("addInputHook", data=(self.cfg["input_hook"]))
        catKey = "ex-1"
        basic_elem = {
            "type": 0,
            "bound": self.cfg["basic_bound"],
            "content": self.cfg["basic"],
        }
        await sio.emit(
            "addElem",
            data=(
                catKey,
                basic_elem,
            ),
        )
        css = self.cfg["css"]
        await sio.emit("insertCSS", data=(catKey, css))
        catKey = "ex-2"
        view_elem = {
            "type": 1,
            "bound": self.cfg["view_bound"],
            "content": self.cfg["view"],
        }
        await sio.emit(
            "addElem",
            data=(
                catKey,
                view_elem,
            ),
        )
        await sio.start_background_task(self.wait_for_elem)
        await sio.sleep(2)
        await sio.emit(
            "hideElem",
            data=(
                catKey,
                view_elem,
            ),
        )
        await sio.sleep(1)
        await sio.emit(
            "showElem",
            data=(
                catKey,
                view_elem,
            ),
        )
        await sio.emit(
            "execJSInElem",
            data=(
                catKey,
                "1 + 2",
            ),
        )
        await sio.sleep(5)
        await sio.emit("delInputHook", data=(self.cfg["input_hook"]))
        await sio.emit(
            "notify",
            data=(
                {
                    "text": "Demo complete. Use `ctrl + c` to exit.",
                    "title": PLUGIN_NAME,
                },
            ),
        )
        await sio.sleep(1)
        print("Demo complete. Use `ctrl + c` to exit.")

    async def loop(self):
        await sio.connect(f"http://localhost:{self.port}")
        await sio.emit("echo", ("Hello World!"))
        await self.test_case()
        await sio.wait()


if __name__ == "__main__":
    # asyncio
    sio = socketio.AsyncClient()
    p = Plugin()
    sio.register_namespace(p.api)
    asyncio.run(p.loop())
