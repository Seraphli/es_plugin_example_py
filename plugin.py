from appdirs import *
import codecs
import json
import asyncio
import socketio
import uuid

APP_NAME = "electron-spirit"


class PluginApi(socketio.AsyncClientNamespace):
    def on_connect(self):
        print("Connected")

    def on_disconnect(self):
        print("Disconnected")

    def on_echo(self, data):
        print("Echo:", data)

    def on_register_topic(self, data):
        print("Register topic:", data)

    def on_insert_css(self, data):
        print("Insert css:", data)

    def on_remove_css(self, data):
        print("Remove css:", data)

    def on_update_elem(self, data):
        print("Update elem:", data)

    def on_remove_elem(self, data):
        print("Remove elem:", data)

    def on_update_bound(self, key, _type, bound):
        print("Update bound:", key, _type, bound)


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
        ctx = {"topic": "foo", "pwd": "test"}
        await sio.emit("register_topic", ctx)
        ctx = {"topic": "bar", "pwd": str(uuid.uuid4())}
        await sio.emit("register_topic", ctx)
        self.ctx = ctx

    async def test_case(self):
        css = ".car { position: relative; width: 100%; height: 100%; padding: 10px; background-color: rgba(250, 250, 250, 200); border: 1px solid black; text-align: center; box-sizing: border-box; overflow: auto; }"
        await sio.emit("insert_css", data=(self.ctx, css))
        await sio.emit(
            "update_elem",
            data=(
                self.ctx,
                {
                    "key": "basic-1",
                    "type": 0,
                    "bound": {"x": 200, "y": 200, "w": 100, "h": 50},
                    "content": "<div class='car'>Hello</div>",
                },
            ),
        )
        await sio.emit(
            "update_elem",
            data=(
                self.ctx,
                {
                    "key": "view-1",
                    "type": 1,
                    "bound": {"x": 300, "y": 300, "w": 300, "h": 300},
                    "content": "https://www.baidu.com",
                },
            ),
        )

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
