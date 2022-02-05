from appdirs import *
import codecs
import json
import asyncio
import socketio
import uuid

APP_NAME = "electron-spirit"
PLUGIN_NAME = "ES Plugin Example"


class PluginApi(socketio.AsyncClientNamespace):
    def __init__(self):
        super().__init__()
        self.elem_count = 0

    def on_connect(self):
        print("Connected")

    def on_disconnect(self):
        print("Disconnected")

    def on_echo(self, data):
        print("Echo:", data)

    def on_register_topic(self, data):
        print("Register topic:", data)

    def on_hook_input(self, data):
        print("Hook input:", data)

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

    def on_process_content(self, content):
        print("Process content:", content)

    def on_mode_flag(self, lock_flag, move_flag, dev_flag):
        print("Mode flag:", lock_flag, move_flag, dev_flag)


class Plugin(object):
    def __init__(self) -> None:
        self.load_config()
        self.api = PluginApi()

    def load_config(self):
        path = user_data_dir(APP_NAME, False, roaming=True)
        with codecs.open(path + "/api.json") as f:
            self.config = json.load(f)
        self.port = self.config["apiPort"]

    async def register(self):
        # Create a context for registering plugins
        # You can either use sample password or use complex password
        # You can also register multiple topic
        ctx = {"topic": "foo", "pwd": str(uuid.uuid4())}
        await sio.emit("register_topic", ctx)
        self.ctx = ctx
        await sio.emit(
            "notify", data=(self.ctx, "Plugin Connected", PLUGIN_NAME, "success", 1500)
        )

    async def wait_for_elem(self):
        while self.api.elem_count < 2:
            await asyncio.sleep(0.1)

    async def test_case(self):
        # get input 'foo' from like '^g foo'
        await sio.emit("input_hook", data=(self.ctx, "g"))
        css = ".car { position: relative; width: 100%; height: 100%; padding: 10px; background-color: rgba(250, 250, 250, 200); border: 1px solid black; text-align: center; box-sizing: border-box; overflow: auto; }"
        await sio.emit("insert_css", data=(self.ctx, css))
        basic_elem = {
            "key": "basic-1",
            "type": 0,
            "bound": {"x": 200, "y": 200, "w": 100, "h": 50},
            "content": "<div class='car'>Hello</div>",
        }
        view_elem = {
            "key": "view-1",
            "type": 1,
            "bound": {"x": 300, "y": 300, "w": 300, "h": 300},
            "content": "https://www.baidu.com",
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
        await sio.emit(
            "notify",
            data=(self.ctx, "Demo complete. Use `ctrl + c` to exit.", PLUGIN_NAME),
        )
        await sio.sleep(5)
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
