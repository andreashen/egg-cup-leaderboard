"""Endpoint discovery for Premier League JSON APIs."""


def build_endpoint_urls(base_url: str, endpoints: dict[str, str]) -> dict[str, str]:
    root = base_url.rstrip("/")
    return {
        name: "{root}/{path}".format(root=root, path=path.lstrip("/"))
        for name, path in endpoints.items()
    }
