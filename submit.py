from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from datetime import datetime, timedelta
import requests
import jwt
import time


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
    manufacturer: str = "",
    model: str = "",
    version: str = ""
) -> (str, str, bool):
    """Returns a tuple of an upload id, asset id, and uploaded bool"""

    print("Authenticating...")
    
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
    print("Requested authentication")
    
    resp.raise_for_status()
    
    data = resp.json()
    expires_in = now + timedelta(seconds=data["expires_in"])

    access_token = data["access_token"]
    claims = jwt.decode(access_token, algorithms=["RS256"], options={"verify_signature": False})

    print("Successfully acquired authentication")
    print("Creating GQL client")

    headers = {
        "Authorization": "Bearer " + access_token,
        "apollographql-client-name": claims["https://netrise.io/org"],
        "apollographql-client-version": "0.8.3",
    }
    client = Client(
        transport=AIOHTTPTransport(
            url=f"{config.endpoint}/graphql/v3",
            headers=headers,
        ),
        fetch_schema_from_transport=True,
        execute_timeout=120,
    )

    print("Created GQL client")
    print("Executing submit query")

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

    print(f"Successfully executed submit query and obtained upload URL: {submit_response['asset']['submit']['uploadUrl']}")
    print("Putting file to URL")
    
    upload_response = requests.put(
        submit_response["asset"]["submit"]["uploadUrl"],
        data=open(path, "rb").read(),
    )
    upload_response.raise_for_status()

    print("Successfully uploaded file")
    print("Polling for asset ID")

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
        print("...")

        poll_response = client.execute(
            poll_query,
            variable_values={
                "args": {
                    "uploadId": upload_id
                }
            },
        )
        uploaded = poll_response["assetUpload"]["uploaded"]
        asset_id = poll_response["assetUpload"]["assetId"]

    print("Obtained asset id!")
    print(f"upload_id: {upload_id}")
    print(f"asset_id: {asset_id}")
    print(f"uploaded: {uploaded}")

    return (upload_id, asset_id, uploaded)
