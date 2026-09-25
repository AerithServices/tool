import asyncio

from textual.app import App, ComposeResult
from textual.widgets import Static

from app.config import get_theme, load_config, set_theme
from app.screens.home import home_view
from app.screens.settings import SettingsScreen
from app.themes import PREBUILT, custom_theme, gradient_art


class AerithApp(App):
    CSS = """
    Screen { background: #000000; }
    #top { align: center top; height: 1fr; }
    #art { width: auto; height: auto; margin-top: 1; }
    #menu { width: 32; margin-top: 2; }
    #bottom { dock: bottom; height: 3; align: left middle; }
    #settings-btn { width: auto; min-width: 12; }
    """
    BINDINGS = [("ctrl+q", "quit", "Quit"), ("q", "quit", "Quit")]

    def __init__(self):
        super().__init__()
        self._frame = 0
        self._store = load_config()

    def compose(self) -> ComposeResult:
        yield from home_view()

    async def on_mount(self) -> None:
        for t in PREBUILT.values():
            self.register_theme(t)
        for c in self._store.get("custom_themes", []):
            try:
                self.register_theme(custom_theme(c["name"], c["primary"], c["background"]))
            except KeyError:
                pass
        saved = get_theme(self._store)
        if saved in self.available_themes:
            self.theme = saved
        elif "aerith" in self.available_themes:
            self.theme = "aerith"
        self.set_interval(0.12, self._tick)

    def apply_theme(self, name):
        if name in self.available_themes:
            self.theme = name
            set_theme(self._store, name)

    def _tick(self) -> None:
        self._frame += 1
        try:
            self.query_one("#art", Static).update(gradient_art(self._frame))
        except Exception:
            pass

    def on_button_pressed(self, event) -> None:
        if event.button.id == "settings-btn":
            self.push_screen(SettingsScreen())


async def amain() -> None:
    await AerithApp().run_async()


def main() -> None:
    asyncio.run(amain())


if __name__ == "__main__":
    main()
