try:
    import compression.zstd as _zstd
    HAS_ZSTD = True
except ImportError:
    _zstd = None
    HAS_ZSTD = False

import zlib

SIG = b"\x28\xb5\x2f\xfd"


def zcompress(data):
    if HAS_ZSTD:
        return _zstd.compress(data)
    return zlib.compress(data)


def zdecompress(data):
    if data[:4] == SIG:
        if not HAS_ZSTD:
            raise RuntimeError("zstd data but compression.zstd missing (need py3.14+)")
        return _zstd.decompress(data)
    return zlib.decompress(data)
