import hashlib
import os
import shutil
import tempfile
import urllib.request
import zlib

from app.utils.compat import zcompress, zdecompress

AGENT = {"User-Agent": "aerith/0.1"}


def _cache_dir():
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        return os.path.join(base, "aerith", "packs")
    base = os.environ.get("XDG_CACHE_HOME") or os.path.join(os.path.expanduser("~"), ".cache")
    return os.path.join(base, "aerith", "packs")


def _cache_get(url, tip):
    key = hashlib.sha1((url + "\x00" + tip).encode()).hexdigest()
    p = os.path.join(_cache_dir(), key)
    if os.path.exists(p):
        with open(p, "rb") as f:
            return zdecompress(f.read())
    return None


def _cache_put(url, tip, pack):
    key = hashlib.sha1((url + "\x00" + tip).encode()).hexdigest()
    p = os.path.join(_cache_dir(), key)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "wb") as f:
        f.write(zcompress(pack))


def _base(url):
    url = url.rstrip("/")
    if url.endswith(".git"):
        url = url[:-4]
    return url + ".git"


def _get(url):
    req = urllib.request.Request(url, headers=AGENT)
    with urllib.request.urlopen(req) as r:
        return r.read()


def _post(url, data):
    req = urllib.request.Request(
        url, data=data, headers=dict(AGENT, **{
            "Content-Type": "application/x-git-upload-pack-request",
            "Accept": "application/x-git-upload-pack-result",
        }))
    with urllib.request.urlopen(req) as r:
        return r.read()


def _read_pkt(data, pos):
    if data[pos:pos + 4] == b"0000":
        return None, pos + 4
    size = int(data[pos:pos + 4], 16)
    line = data[pos + 4:pos + size]
    return line, pos + size


def ls_remote(url):
    base = _base(url)
    data = _get(base + "/info/refs?service=git-upload-pack")
    pos = 0
    line, pos = _read_pkt(data, pos)
    assert line == b"# service=git-upload-pack\n", "not a git server"
    assert _read_pkt(data, pos)[0] is None
    pos += 4
    refs, caps, head_branch = {}, [], None
    while pos < len(data):
        line, pos = _read_pkt(data, pos)
        if line is None:
            break
        line = line.rstrip(b"\n")
        if b"\x00" in line:
            head, capbytes = line.split(b"\x00", 1)
            caps = capbytes.decode().split()
            line = head
        sha, name = line.decode().split(" ", 1)
        refs[name] = sha
    for c in caps:
        if c.startswith("symref=HEAD:"):
            head_branch = c.split(":", 1)[1]
    return refs, head_branch


def _fetch_pack(base, shas):
    caps = "multi_ack ofs-delta"
    body = b""
    first = True
    for s in shas:
        line = ("want %s\x00%s\n" % (s, caps)).encode() if first else ("want %s\n" % s).encode()
        body += ("%04x" % (len(line) + 4)).encode() + line
        first = False
    body += b"0000" + b"0009done\n"
    data = _post(base + "/git-upload-pack", body)
    pos = 0
    while pos < len(data):
        if data[pos:pos + 4] == b"PACK":
            break
        line, pos = _read_pkt(data, pos)
        if line is None:
            continue
    return data[pos:]


def _read_varint(data, pos):
    out, shift = 0, 0
    while True:
        b = data[pos]
        pos += 1
        out |= (b & 0x7f) << shift
        shift += 7
        if not b & 0x80:
            return out, pos


def _read_obj_header(data, pos):
    b = data[pos]
    pos += 1
    otype = (b >> 4) & 7
    size = b & 15
    shift = 4
    while b & 0x80:
        b = data[pos]
        pos += 1
        size |= (b & 0x7f) << shift
        shift += 7
    return otype, size, pos


def _apply_delta(base, delta):
    pos = 0
    _, pos = _read_varint(delta, pos)
    outlen, pos = _read_varint(delta, pos)
    out = bytearray()
    while pos < len(delta):
        cmd = delta[pos]
        pos += 1
        if cmd & 0x80:
            off, size = 0, 0
            for i in range(4):
                if cmd & (1 << i):
                    off |= delta[pos] << (i * 8)
                    pos += 1
            for i in range(3):
                if cmd & (1 << (4 + i)):
                    size |= delta[pos] << (i * 8)
                    pos += 1
            if size == 0:
                size = 0x10000
            out += base[off:off + size]
        elif cmd:
            out += delta[pos:pos + cmd]
            pos += cmd
    assert len(out) == outlen, "bad delta"
    return bytes(out)


def parse_pack(pack):
    assert pack[:4] == b"PACK"
    count = int.from_bytes(pack[8:12], "big")
    pos = 12
    objs = {}
    pending = []
    offsets = {}
    for _ in range(count):
        start = pos
        otype, _, pos = _read_obj_header(pack, pos)
        if otype == 6:  # ofs-delta
            off, pos = _read_varint(pack, pos)
            raw, pos = _inflate(pack, pos)
            pending.append((start, start - off, raw))
        elif otype == 7:  # ref-delta
            ref = pack[pos:pos + 20].hex()
            pos += 20
            raw, pos = _inflate(pack, pos)
            pending.append((start, ref, raw))
        else:
            kind = {1: "commit", 2: "tree", 3: "blob", 4: "tag"}[otype]
            raw, pos = _inflate(pack, pos)
            sha = _oid(kind, raw)
            objs[sha] = (kind, raw)
            offsets[start] = sha
    while pending:
        stuck = True
        for start, base, raw in list(pending):
            sha = base if isinstance(base, str) else offsets.get(base)
            if sha is None and isinstance(base, int):
                sha = _try_read_base(pack, objs, offsets, base)
            if sha is None or sha not in objs:
                continue
            kind, base_raw = objs[sha]
            full = _apply_delta(base_raw, raw)
            sha = _oid(kind, full)
            objs[sha] = (kind, full)
            offsets[start] = sha
            pending.remove((start, base, raw))
            stuck = False
        if stuck:
            raise ValueError("unresolvable delta")
    return objs


def _try_read_base(pack, objs, offsets, base_pos):
    otype, _, pos = _read_obj_header(pack, base_pos)
    if otype in (6, 7):
        return None
    kind = {1: "commit", 2: "tree", 3: "blob", 4: "tag"}[otype]
    raw, _ = _inflate(pack, pos)
    sha = _oid(kind, raw)
    objs[sha] = (kind, raw)
    offsets[base_pos] = sha
    return sha


def _inflate(pack, pos):
    d = zlib.decompressobj()
    out = b""
    while True:
        chunk = pack[pos:pos + 4096]
        pos += len(chunk)
        out += d.decompress(chunk)
        if d.eof:
            break
    unused = len(d.unused_data)
    return out, pos - unused


def _oid(kind, raw):
    h = hashlib.sha1()
    h.update(("%s %d\x00" % (kind, len(raw))).encode() + raw)
    return h.hexdigest()


def parse_tree(raw):
    out = []
    pos = 0
    while pos < len(raw):
        sp = raw.index(b" ", pos)
        nul = raw.index(b"\x00", sp)
        mode = raw[pos:sp].decode()
        name = raw[sp + 1:nul].decode()
        sha = raw[nul + 1:nul + 21].hex()
        out.append((mode, name, sha))
        pos = nul + 21
    return out


def commit_tree(objs, commit_sha):
    for line in objs[commit_sha][1].decode().split("\n"):
        if line.startswith("tree "):
            return line[5:45]
    raise ValueError("no tree in commit")


class Repo:
    def __init__(self, workdir, objs):
        self.workdir = os.path.abspath(workdir)
        self.objs = objs

    @classmethod
    def clone(cls, url, dest=None, ref=None):
        refs, head_branch = ls_remote(url)
        if ref is None:
            branch = head_branch or "refs/heads/main"
            want = [refs[branch]] if branch in refs else [refs["HEAD"]]
        elif ref in refs:
            want = [refs[ref]]
        else:
            want = [ref]
        pack = _cache_get(url, want[0])
        if pack is None:
            pack = _fetch_pack(_base(url), want)
            _cache_put(url, want[0], pack)
        objs = parse_pack(pack)
        dest = os.path.abspath(dest or tempfile.mkdtemp(prefix="aerith-clone-"))
        gitdir = os.path.join(dest, ".git", "objects")
        os.makedirs(gitdir, exist_ok=True)
        for sha, (kind, raw) in objs.items():
            p = os.path.join(gitdir, sha[:2], sha[2:])
            if not os.path.exists(p):
                os.makedirs(os.path.dirname(p), exist_ok=True)
                with open(p, "wb") as f:
                    f.write(zlib.compress(("%s %d\x00" % (kind, len(raw))).encode() + raw))
        repo = cls(dest, objs)
        repo.checkout(want[0])
        return repo

    def _blob(self, sha):
        kind, raw = self.objs[sha]
        assert kind == "blob"
        return raw

    def _walk(self, tree_sha, prefix=""):
        for mode, name, sha in parse_tree(self.objs[tree_sha][1]):
            path = os.path.join(prefix, name) if prefix else name
            if mode == "40000":
                yield from self._walk(sha, path)
            else:
                yield path, mode, sha

    def checkout(self, commit_sha):
        tree = commit_tree(self.objs, commit_sha)
        for path, mode, sha in self._walk(tree):
            full = os.path.join(self.workdir, path)
            os.makedirs(os.path.dirname(full) or self.workdir, exist_ok=True)
            data = self._blob(sha)
            with open(full, "wb") as f:
                f.write(data.replace(b"\r\n", b"\n") if mode != "120000" else data)

    def read(self, path):
        with open(os.path.join(self.workdir, path), "rb") as f:
            return f.read()

    def write(self, path, data):
        if isinstance(data, str):
            data = data.encode()
        full = os.path.join(self.workdir, path)
        os.makedirs(os.path.dirname(full) or self.workdir, exist_ok=True)
        with open(full, "wb") as f:
            f.write(data)

    def list_files(self):
        out = []
        for root, _, files in os.walk(self.workdir):
            if ".git" in root:
                continue
            for fn in files:
                out.append(os.path.relpath(os.path.join(root, fn), self.workdir))
        return sorted(out)


def fetch_file(url, path, ref=None):
    tmp = tempfile.mkdtemp(prefix="aerith-fetch-")
    try:
        repo = Repo.clone(url, dest=tmp, ref=ref)
        return repo.read(path.lstrip("/"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
