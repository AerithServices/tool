
import asyncio

from textual.app import App, ComposeResult
from textual.widgets import Static

ART = r"""██▀▄▄ ▄█▀ ██▀▄▄ ▄▄ ▀██▀ ▄▄ ▄▄
██ ██ ██  ██ █▀ ██  ██  ██ ██
██▀██ ██▀ ██▀█▄ ██  ██  ██▀██
██ ██ ██  ██ ██ ██  ██  ██ ██
██ ██ ▀█▄ ██ ██ ██  ██  ██ ██"""


class AerithApp(App):
    CSS = """
    Screen { align: center top; }
    #art { width: auto; height: auto; color: $primary; margin-top: 1; }
    """
    BINDINGS = [("ctrl+q", "quit", "Quit"), ("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Static(ART, id="art")

    async def on_mount(self) -> None:
        pass

    async def _background_task(self) -> None:
        await asyncio.sleep(0)


async def amain() -> None:
    app = AerithApp()
    await app.run_async()


def main() -> None:
    asyncio.run(amain())


if __name__ == "__main__":
    main()
