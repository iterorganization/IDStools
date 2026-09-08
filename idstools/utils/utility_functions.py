import logging
from urllib.parse import urlsplit, urlunsplit

logger = logging.getLogger(f"module.{__name__}")


def add_query_to_uri(uri: str, *, query: str, backend=None):
    """Add a query to the URI.

    If a backend is given, add the query only when it matches the URI's
    backend. Otherwise, return the original URI unchanged. When backend is
    None, add the query to any URI.
    """
    uri_parts = urlsplit(uri)
    uri_backend = uri_parts.path.rsplit("/", 1)[-1]
    if backend is not None and uri_backend != backend:
        return uri

    key = query.split("=", 1)[0]
    if any(item.split("=", 1)[0] == key for item in uri_parts.query.split(";")):
        return uri
    updated_query = f"{uri_parts.query};{query}" if uri_parts.query else query
    return urlunsplit(
        (
            uri_parts.scheme,
            uri_parts.netloc,
            uri_parts.path,
            updated_query,
            uri_parts.fragment,
        )
    )


def get_slice_from_array(arr, slice_str):
    if ":" not in slice_str:
        index = int(slice_str)
        try:
            return [arr[index]]
        except IndexError:
            logger.error(f"Index {index} out of bounds for array of size {len(arr)}")
            return None

    parts = slice_str.split(":")

    start = int(parts[0]) if parts[0] else None
    stop = int(parts[1]) if len(parts) > 1 and parts[1] else None
    step = int(parts[2]) if len(parts) > 2 and parts[2] else None

    slice_obj = slice(start, stop, step)

    return arr[slice_obj]
