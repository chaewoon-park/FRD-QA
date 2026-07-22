"""Shim: zstd API backed by zstandard (prebuilt wheel)."""
import zstandard


def decompress(data: bytes) -> bytes:
    dctx = zstandard.ZstdDecompressor()
    try:
        return dctx.decompress(data)
    except zstandard.ZstdError:
        # frame without content size — stream decompress
        import io
        out = io.BytesIO()
        with dctx.stream_reader(io.BytesIO(data)) as r:
            while True:
                chunk = r.read(1 << 20)
                if not chunk:
                    break
                out.write(chunk)
        return out.getvalue()
