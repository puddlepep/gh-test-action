import os
from auth import Config, create_client, submit, wait_for_processing


class Output:
    def __init__(self):
        self.asset_id = ''
        self.upload_id = ''
        self.uploaded = False

    def write(self):
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            print(f'asset-id={self.asset_id}', file=f)
            print(f'upload-id={self.upload_id}', file=f)
            print(f'uploaded={self.uploaded}', file=f)
OUTPUT = Output()


def error(msg: str, title: str = ""):
    OUTPUT.write()
    print(f"::error title={title}::{msg}")
    exit(1)


def get_input(env: str, required: bool):
    value = os.getenv(env, None)

    if value is None and required:
        error(f"Input '{env}' is required.", "BAD INPUT")
    return value


def main():

    # create config with auth inputs
    config = Config(
        get_input('TOKEN_URL', True),
        get_input('CLIENT_SECRET', True),
        get_input('AUDIENCE', True),
        get_input('CLIENT_ID', True),
        get_input('ORGANIZATION_ID', True),
        get_input('ENDPOINT', True)
    )

    # collect asset inputs
    artifact_path = get_input('ARTIFACT_PATH', True)
    name = get_input('NAME', True)
    manufacturer = get_input('MANUFACTURER', False)
    model = get_input('MODEL', False)
    version = get_input('VERSION', False)
    
    # log OK and collected asset info
    print("Inputs OK!")
    print(f"Submitting '{artifact_path}' as '{name}'")
    if manufacturer: print(f"Manufacturer: '{manufacturer}'")
    if model: print(f"Model: '{model}'")
    if version: print(f"Version: '{version}'")

    # create gql client
    try:
        client = create_client(config)
    except Exception as e:
        error(str(e), f"Failed to create client: {e.__class__}")
    print("Created client")
    
    # submit and assign outputs
    try:
        OUTPUT.upload_id, OUTPUT.asset_id, OUTPUT.uploaded = submit(client, artifact_path, name, manufacturer, model, version)
    except Exception as e:
        error(str(e), f"Failed to submit asset: {e.__class__}")
    if not OUTPUT.asset_id:
        error("Failed to get asset ID")

    # wait for the asset to finish processing and print the result
    print("Waiting for asset to finish processing...")

    try:
        processed_successfully = wait_for_processing(client, asset_id)
        if processed_successfully:
            print("Asset successfully processed.")
        else:
            error("Failed to process asset")
    except Exception as e:
        error(str(e), e.__class__)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        error(str(e), e.__class__)

    OUTPUT.write()

