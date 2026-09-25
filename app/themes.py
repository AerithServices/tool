from rich.text import Text
from textual.theme import Theme

ART = r"""██▀▄▄ ▄█▀ ██▀▄▄ ▄▄ ▀██▀ ▄▄ ▄▄
██ ██ ██  ██ █▀ ██  ██  ██ ██
██▀██ ██▀ ██▀█▄ ██  ██  ██▀██
██ ██ ██  ██ ██ ██  ██  ██ ██
██ ██ ▀█▄ ██ ██ ██  ██  ██ ██"""

STOPS = ["#6d28d9", "#8b5cf6", "#a855f7", "#c084fc", "#e9d5ff", "#c084fc", "#a855f7", "#8b5cf6"]

PREBUILT = {
    "aerith": Theme(name="aerith", primary="#a855f7", secondary="#7c3aed",
                    accent="#c084fc", foreground="#e9d5ff", background="#000000",
                    surface="#0a0a0f", panel="#111118", dark=True),
    "blood": Theme(name="blood", primary="#ef4444", secondary="#991b1b",
                   accent="#fca5a5", foreground="#fee2e2", background="#000000",
                   surface="#0f0a0a", panel="#181111", dark=True),
    "ocean": Theme(name="ocean", primary="#22d3ee", secondary="#0e7490",
                   accent="#67e8f9", foreground="#cffafe", background="#000000",
                   surface="#0a0f14", panel="#111820", dark=True),
    "forest": Theme(name="forest", primary="#22c55e", secondary="#15803d",
                    accent="#86efac", foreground="#dcfce7", background="#000000",
                    surface="#0a0f0b", panel="#111814", dark=True),
}


def gradient_art(offset):
    lines = ART.split("\n")
    width = max(len(l) for l in lines)
    out = Text()
    for line in lines:
        for x, ch in enumerate(line.ljust(width)):
            out.append(ch, style=STOPS[(x + offset) % len(STOPS)])
        out.append("\n")
    return out


def custom_theme(name, primary, background, accent=""):
    return Theme(name=name, primary=primary, secondary=primary,
                 accent=accent or primary, foreground="#e5e5e5",
                 background=background, surface=background,
                 panel=background, dark=True)
