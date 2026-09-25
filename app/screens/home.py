from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Select, Static

from app.themes import gradient_art


def home_view() -> ComposeResult:
    with Vertical(id="top"):
        yield Static(gradient_art(0), id="art")
        yield Select(
            [("nuke and raid bots", "nuke and raid bots")],
            prompt="Select an option",
            id="menu",
        )
    with Horizontal(id="bottom"):
        yield Button("\u2699", id="settings-btn")


class Home(Static):
    pass
