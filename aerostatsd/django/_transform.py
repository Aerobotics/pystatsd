from urllib.parse import urlparse


def normalize_url_path(url: str) -> str:
    """
    'Normalizes' a URL's path

    The objective here is to remove resource specific identifiers from
    a URL path. The reason being, in Grafana, each URL path is a separate
    metric. However, this creates too much noise for endpoints with
    identifiers e.g `GET /users/12345`.

    Instead, we would like to 'normalize' it by removing the ID and replacing
    it with `:id`. A path `/users/12345` will become `/users/:id`. This will
    effectively group them all under one metric.

    Parameters
    ----------
    url
        The URL path to normalize

    Returns
    -------
    str
        The normalized url path
    """
    parsed_url = urlparse(url)
    path = parsed_url.path.split("/")
    query = parsed_url.query
    
    normalized_path = [p if not p.isdigit() else "{id}" for p in path]
    normalized_path = "/".join(normalized_path)
    if query:
        normalized_path = f"{normalized_path}?{query}"

    return normalized_path
