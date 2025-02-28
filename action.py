import os
from submit import Config, submit


def add_output(key: str, value: str):
    with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
        print(f'{key}={value}', file=f)


def main():

    # create config with auth inputs
    config = Config(
        os.environ['TOKEN_URL'],
        os.environ['CLIENT_SECRET'],
        os.environ['AUDIENCE'],
        os.environ['CLIENT_ID'],
        os.environ['ORGANIZATION_ID'],
        os.environ['ENDPOINT']
    )
    
    # collect asset inputs
    artifact_path = os.environ['ARTIFACT_PATH']
    asset_name = os.environ['NAME']
    manufacturer = os.getenv('MANUFACTURER', '')
    model = os.getenv('MODEL', '')
    version = os.getenv('VERSION', '')
    
    print('OK!')
    print(f'Created config')
    print(f'Submitting "{artifact_path}" as "{asset_name}"')

    if manufacturer or model or version:
        print(f'Manufacturer: "{manufacturer}"') if manufacturer else ''
        print(f'Model: "{model}"') if model else ''
        print(f'Version: "{version}"') if version else ''

    # submit and assign outputs
    upload_id, asset_id, uploaded = submit(config, artifact_path, asset_name, manufacturer, model, version)
    add_output('upload-id', upload_id)
    add_output('asset-id', asset_id)
    add_output('uploaded', str(uploaded))


if __name__ == '__main__':
    main()

