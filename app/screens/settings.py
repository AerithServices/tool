from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Select

from app.themes import PREBUILT, custom_theme


class ThemeScreen(Screen):
    CSS = """
    ThemeScreen { align: center middle; }
    #box { width: 60; height: auto; border: solid $primary; padding: 1 2; }
    #box Label { margin-top: 1; }
    #row { height: auto; margin-top: 1; }
    #row Button { margin-right: 1; }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="box"):
            yield Label("Theme")
            yield Select([], id="theme-select", prompt="pick a theme")
            yield Label("Custom theme (hex, e.g. #a855f7)")
            yield Input(placeholder="name", id="c-name")
            yield Input(placeholder="primary #a855f7", id="c-primary")
            yield Input(placeholder="background #000000", id="c-bg")
            with Horizontal(id="row"):
                yield Button("Save custom", id="save-custom", variant="primary")
                yield Button("Back", id="back")

    def on_mount(self) -> None:
        app = self.app
        sel = self.query_one("#theme-select", Select)
        names = list(PREBUILT) + [t for t in app.available_themes if t not in PREBUILT]
        names += [c["name"] for c in app._store.get("custom_themes", [])]
        seen, opts = set(), []
        for n in names:
            if n not in seen:
                seen.add(n)
                opts.append((n, n))
        sel.set_options(opts)
        sel.value = app.theme

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "theme-select" and event.value != Select.BLANK:
            self.app.apply_theme(str(event.value))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        app = self.app
        if event.button.id == "back":
            app.pop_screen()
        elif event.button.id == "save-custom":
            q = self.query_one
            name = q("#c-name", Input).value.strip()
            primary = q("#c-primary", Input).value.strip() or "#a855f7"
            bg = q("#c-bg", Input).value.strip() or "#000000"
            if not name:
                return
            customs = [c for c in app._store.get("custom_themes", []) if c["name"] != name]
            customs.append({"name": name, "primary": primary, "background": bg})
            app._store.set("custom_themes", customs)
            app.register_theme(custom_theme(name, primary, bg))
            sel = q("#theme-select", Select)
            sel.set_options(sel._options + [(name, name)])
            sel.value = name
            app.apply_theme(name)


class SettingsScreen(Screen):
    CSS = """
    SettingsScreen { align: center middle; }
    #box { width: 40; height: auto; border: solid $primary; padding: 1 2; }
    #row { height: auto; margin-top: 1; }
    #row Button { margin-right: 1; }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="box"):
            yield Label("Settings")
            with Horizontal(id="row"):
                yield Button("Theme", id="open-theme", variant="primary")
                yield Button("Back", id="back")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
        elif event.button.id == "open-theme":
            self.app.push_screen(ThemeScreen())
