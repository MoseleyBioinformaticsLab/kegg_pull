import requests as rq

from . import kegg_url as ku


def single_pull(kegg_url: ku.AbstractKEGGurl, timeout: int = 60, n_tries: int = 3) -> rq.Response:
    n_times_tried: int = 0

    while n_times_tried < n_tries:
        n_times_tried += 1
        res: rq.Response = rq.get(kegg_url.url, timeout=timeout)

        if res.status_code == 200:
            return res

    return None
