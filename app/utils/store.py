import json
import os
import tempfile


class JsonStore:
    def __init__(self, path, defaults=None):
        self.path = os.path.abspath(path)
        self._data = dict(defaults or {})
        self.load()

    def load(self):
        try:
            with open(self.path) as f:
                data = json.load(f)
            if isinstance(data, dict):
                self._data.update(data)
        except (FileNotFoundError, ValueError, OSError):
            pass
        return self._data

    def save(self):
        folder = os.path.dirname(self.path) or "."
        os.makedirs(folder, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=folder, suffix=".tmp")
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(self._data, f, indent=2)
            os.replace(tmp, self.path)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value, save=True):
        self._data[key] = value
        if save:
            self.save()

    def delete(self, key, save=True):
        self._data.pop(key, None)
        if save:
            self.save()

    def all(self):
        return dict(self._data)


def default_store_path(app_name="aerith"):
    if os.name == "nt":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        return os.path.join(base, app_name, "store.json")
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(base, app_name, "store.json")
