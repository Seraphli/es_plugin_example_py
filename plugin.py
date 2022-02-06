from appdirs import *
import codecs
import json
import asyncio
import socketio
import uuid

APP_NAME = "electron-spirit"
PLUGIN_NAME = "ES Plugin Example"
SHORT_NAME = "example"
PLUGIN_SETTING = "plugin.setting.json"


class PluginApi(socketio.AsyncClientNamespace):
    def __init__(self, parent):
        super().__init__()
        self.elem_count = 0
        self.parent = parent

    def on_connect(self):
        print("Connected")

    def on_disconnect(self):
        print("Disconnected")

    def on_echo(self, data):
        print("Echo:", data)

    def on_register_topic(self, data):
        print("Register topic:", data)

    def on_add_input_hook(self, data):
        print("Add input hook:", data)

    def on_del_input_hook(self, data):
        print("Del input hook:", data)

    def on_insert_css(self, data):
        print("Insert css:", data)

    def on_remove_css(self, data):
        print("Remove css:", data)

    def on_update_elem(self, data):
        print("Update elem:", data)
        self.elem_count += 1

    def on_remove_elem(self, data):
        print("Remove elem:", data)
        self.elem_count -= 1

    def on_show_view(self, data):
        print("Show view:", data)

    def on_hide_view(self, data):
        print("Hide view:", data)

    def on_exec_js_in_elem(self, data):
        print("Exec js in elem:", data)

    def on_notify(self, data):
        print("Notify:", data)

    def on_update_bound(self, key, _type, bound):
        print("Update bound:", key, _type, bound)
        self.parent.update_bound(key, _type, bound)

    def on_process_content(self, content):
        print("Process content:", content)

    def on_mode_flag(self, lock_flag, move_flag, dev_flag):
        print("Mode flag:", lock_flag, move_flag, dev_flag)


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
        except:
            self.cfg = {
                "input_hook": "g",
                "css": ".car { position: relative; width: 100%; height: 100%; padding: 10px; background-color: rgba(250, 250, 250, 200); border: 1px solid black; text-align: center; box-sizing: border-box; overflow: auto; }",
                "basic": "<div class='car'>Hello</div>",
                "basic_bound": {"x": 200, "y": 200, "w": 100, "h": 50},
                "view": "https://www.baidu.com",
                "view_bound": {"x": 300, "y": 300, "w": 300, "h": 300},
            }
        self.save_cfg()

    def save_cfg(self):
        with codecs.open(PLUGIN_SETTING, "w") as f:
            json.dump(self.cfg, f)
    
    def update_bound(self, key, _type, bound):
        if key == "basic-1":
            self.cfg["basic_bound"] = bound
        elif key == "view-1":
            self.cfg["view_bound"] = bound
        self.save_cfg()

    async def register(self):
        # Create a context for registering plugins
        # You can either use sample password or use complex password
        # You can also register multiple topic
        ctx = {"topic": SHORT_NAME, "pwd": str(uuid.uuid4())}
        await sio.emit("register_topic", ctx)
        self.ctx = ctx

    async def wait_for_elem(self):
        while self.api.elem_count < 2:
            await asyncio.sleep(0.1)

    async def test_case(self):
        # get input 'foo' from like '!g foo'
        await sio.emit("add_input_hook", data=(self.ctx, self.cfg["input_hook"]))
        css = self.cfg["css"]
        await sio.emit("insert_css", data=(self.ctx, css))
        basic_elem = {
            "key": "basic-1",
            "type": 0,
            "bound": self.cfg["basic_bound"],
            "content": self.cfg["basic"],
        }
        view_elem = {
            "key": "view-1",
            "type": 1,
            "bound": self.cfg["view_bound"],
            "content": self.cfg["view"],
        }
        await sio.emit(
            "update_elem",
            data=(
                self.ctx,
                basic_elem,
            ),
        )
        await sio.emit(
            "update_elem",
            data=(
                self.ctx,
                view_elem,
            ),
        )
        await sio.start_background_task(self.wait_for_elem)
        await sio.emit(
            "hide_view",
            data=(
                self.ctx,
                view_elem,
            ),
        )
        await sio.sleep(1)
        await sio.emit(
            "show_view",
            data=(
                self.ctx,
                view_elem,
            ),
        )
        await sio.emit(
            "exec_js_in_elem",
            data=(
                self.ctx,
                {
                    "key": "view-1",
                    "type": 1,
                    "bound": {"x": -1, "y": -1, "w": -1, "h": -1},
                    "content": "https://www.baidu.com",
                },
                "1 + 2",
            ),
        )
        await sio.sleep(5)
        await sio.emit("del_input_hook", data=(self.ctx, self.cfg["input_hook"]))
        await sio.emit(
            "notify",
            data=(self.ctx, "Demo complete. Use `ctrl + c` to exit.", PLUGIN_NAME),
        )
        await sio.sleep(1)
        print("Demo complete. Use `ctrl + c` to exit.")

    async def loop(self):
        await sio.connect(f"http://localhost:{self.port}")
        await sio.emit("echo", "Hello World!")
        await self.register()
        await self.test_case()
        await sio.wait()


if __name__ == "__main__":
    # asyncio
    sio = socketio.AsyncClient()
    p = Plugin()
    sio.register_namespace(p.api)
    asyncio.run(p.loop())
