from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from datetime import datetime, timedelta
import requests
import jwt
import time


class AuthException(Exception): pass
class SubmitAssetException(Exception): pass


class Config:
    def __init__(self, token_url, client_secret, audience, client_id, organization_id, endpoint):
        self.token_url = token_url
        self.client_secret = client_secret
        self.audience = audience
        self.client_id = client_id
        self.organization_id = organization_id
        self.endpoint = endpoint


def create_client(config: Config) -> Client:
    try:
        print("Authenticating...")

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

    except requests.HTTPError as e:
        raise AuthException(f"Failed to authenticate: {e}")

    print("Successfully authenticated")

    headers = {
        "Authorization": "Bearer " + access_token,
        "apollographql-client-name": claims["https://netrise.io/org"],
        "apollographql-client-version": "GitHub Action",
    }
    return Client(
        transport=AIOHTTPTransport(
            url=f"{config.endpoint}/graphql/v3",
            headers=headers,
        ),
        fetch_schema_from_transport=True,
        execute_timeout=120,
    )


def submit(
    client: Client,
    path: str,
    name: str,
    manufacturer: str = "",
    model: str = "",
    version: str = ""
) -> (str, str, bool):
    """Submits an asset and returns a tuple of an upload id, asset id, and uploaded bool"""

    print("Submitting asset...")

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
    if 'errors' in submit_response:
        raise SubmitAssetException(f"Failed to execute submit query: {submit_response.errors}")

    upload_id = submit_response["asset"]["submit"]["uploadId"] 

    try:
        upload_response = requests.put(
            submit_response["asset"]["submit"]["uploadUrl"],
            data=open(path, "rb").read(),
        )
        upload_response.raise_for_status()
    except requests.HTTPError as e:
        raise SubmitAssetException(f"Failed to submit asset: {e}")

    print("Successfully submitted asset")

    # get asset ID
    asset_id = ""
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

    # continually poll for asset ID until it is available
    try:
        uploaded = False
        while not uploaded:
            time.sleep(2)

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
    except Exception as e: pass

    return (upload_id, asset_id, uploaded)


def wait_for_processing(client: Client, asset_id: str) -> bool:
    """Waits for an asset to finish processing, and returns True if it was successful"""
    
    query = gql(
        """
        query GetStatus($args: AssetInput!) {
            asset(args: $args) {
                status
            }
        }
        """
    )

    status = "INPROGRESS"
    while status == "INPROGRESS":
        response = client.execute(query, {"args": {"assetId": asset_id}})
        status = response["asset"]["status"]

    if status == "SUCCESS":
        return True
    return False
