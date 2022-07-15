from src.kegg_pull.kegg_url import AbstractKEGGurl
from requests import get, Response


def pull_single_from_kegg(kegg_url: AbstractKEGGurl, timeout: int = 60, n_tries: int = 3) -> Response:
    n_times_tried: int = 0

    while n_times_tried < n_tries:
        n_times_tried += 1
        res: Response = get(kegg_url.url, timeout=timeout)

        if res.status_code == 200:
            return res

    return None
