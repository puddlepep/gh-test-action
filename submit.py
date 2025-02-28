from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from datetime import datetime
import requests
import jwt


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
    path: str,
    name: str,
    manufacturer: str = '',
    model: str = '',
    version: str = ''
) -> (str, str, bool):
    """Returns a tuple of an upload id, asset id, and uploaded bool"""

    # authenticate and create a gql client
    payload = (
        "grant_type=client_credentials&client_id="
        + config.client_id
        + "&client_secret="
        + config.client_secret
        + "&audience="
        + config.audience
        + "&organization="
        + config.organization_id
    )
    headers = {"content-type": "application/x-www-form-urlencoded"}
    now = datetime.now()
    resp = requests.post(
        config.token_url,
        data=payload,
        headers=headers,
    )
    resp.raise_for_status()
    data = resp.json()
    expires_in = now + timedelta(seconds=data["expires_in"])

    access_token = data["access_token"]
    claims = jwt.decode(access_token, algorithms=["RS256"], options={"verify_signature": False})

    headers = {
        "Authorization": "Bearer " + access_token,
        "apollographql-client-name": self.org,
        "apollographql-client-version": '0.8.3',
    }
    client = Client(
        transport=AIOHTTPTransport(
            url=f"{config.endpoint}/graphql/v3",
            headers=headers,
        ),
        fetch_schema_from_transport=True,
        execute_timeout=120,
    )

    # submit the artifact to NetRise
    submit_response = client.execute(
        gql(
            """
            mutation SubmitAsset($fileName: String!, $args: SubmitAssetInput) {
                asset {
                    submit(fileName: $fileName, args: $args) {
                        uploadUrl
                        uploadId
                    }
                }
            }
            """
        ),
        variable_values={
            "fileName": path,
            "args": {
                "name": name,
                "model": model,
                "manufacturer": manufacturer,
                "version": version
            },
        },
    )
    upload_response = requests.put(
        submit_response["asset"]["submit"]["uploadUrl"],
        data=open(path, "rb").read(),
        verify=self.config.enable_ssl,
    )
    upload_response.raise_for_status()

    # get asset ID
    poll_query = gql(
        """
        query AssetUpload($args: AssetUploadInput) {
            assetUpload(args: $args) {
                uploadId
                assetId
                uploaded
            }
        }
        """
    )

    upload_id = submit_response["asset"]["submit"]["uploadId"] 

    # continually poll for asset ID until it is available
    asset_id = ""
    uploaded = False
    while not uploaded:
        time.sleep(2)
        poll_response = self.execute(
            poll_query,
            variable_values={
                "args": {
                    "uploadId": upload_id
                }
            },
        )
        uploaded = poll_response["assetUpload"]["uploaded"]
        asset_id = poll_response["assetUpload"]["assetId"]


    return (upload_id, asset_id, uploaded)
