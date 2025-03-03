from urllib.parse import urlparse
from uuid import UUID


def normalize_url_path(url: str, include_query_params: bool = True) -> str:
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

    include_query_params
        Whether to include query parameters in the normalized path

    Returns
    -------
    str
        The normalized url path
    """
    parsed_url = urlparse(url)
    path = parsed_url.path.split("/")
    query = parsed_url.query

    normalized_path_parts = []
    for p in path:
        if p.isdigit():
            normalized_path_parts.append("{id}")
        elif is_uuid(p):
            normalized_path_parts.append("{uuid}")
        else:
            normalized_path_parts.append(p)

    normalized_path = "/".join(normalized_path_parts)
    if query and include_query_params:
        normalized_path = f"{normalized_path}?{query}"

    return normalized_path


def is_uuid(uuid_to_test: str, version=4):
    """
    Check if uuid_to_test is a valid UUID.

     Parameters
    ----------
    uuid_to_test : str
    version : {1, 2, 3, 4}

     Returns
    -------
    `True` if uuid_to_test is a valid UUID, otherwise `False`.

     Examples
    --------
    >>> is_valid_uuid('c9bf9e57-1685-4c89-bafb-ff5af830be8a')
    True
    >>> is_valid_uuid('c9bf9e58')
    False
    """

    try:
        uuid_obj = UUID(uuid_to_test, version=version)
    except ValueError:
        return False

    return str(uuid_obj) == uuid_to_test
