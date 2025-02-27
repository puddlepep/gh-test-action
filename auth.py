class Config:
    def __init__(self, token_url, client_secret, audience, client_id, organization_id, endpoint):
        self.token_url = token_url
        self.client_secret = client_secret
        self.audience = audience
        self.client_id = client_id
        self.organization_id = organization_id
        self.endpoint = endpoint


def submit(
    config: Config,
    name: str,
    manufacturer: str = '',
    model: str = '',
    version: str = ''
) -> (str, str, bool):
    """Returns a tuple of an upload id, asset id, and uploaded bool"""

    return ("PEPMENAWKSAWIS", "weeewooo", True)
