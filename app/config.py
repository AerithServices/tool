import os
import shutil

from app.utils.store import JsonStore

CONFIG_FILENAME = "config.json"
LEGACY_NAMES = ("CONFIG.JSON",)


def legacy_path():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(os.path.dirname(here), "CONFIG.JSON")


def config_path():
    if os.name == "nt":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        return os.path.join(base, "aerith", CONFIG_FILENAME)
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(base, "aerith", CONFIG_FILENAME)


def load_config(path=None):
    target = path or config_path()
    if path is None:
        folder = os.path.dirname(target)
        olds = [legacy_path()] + [os.path.join(folder, n) for n in LEGACY_NAMES]
        for old in olds:
            if old != target and os.path.exists(old) and not os.path.exists(target):
                os.makedirs(folder, exist_ok=True)
                shutil.move(old, target)
                break
    store = JsonStore(target, defaults=dict(DEFAULTS))
    if not os.path.exists(store.path):
        store.save()
    return store


DEFAULTS = {
    "theme": "aerith",
    "custom_themes": [],
}


def get_theme(store):
    theme = store.get("theme", DEFAULTS["theme"])
    return str(theme) if theme else DEFAULTS["theme"]


def set_theme(store, theme):
    store.set("theme", theme)
