import os


def add_output(key: str, value: str):
    with open(os.envoron['GITHUB_OUTPUT'], 'a') as f:
        print(f'{key}={value}', file=f)


def main():

    # collect required inputs
    config_path = os.getenv('CONFIG_PATH', None)
    artifact_path = os.getenv('ARTIFACT_PATH', None)
    asset_name = os.getenv('NAME', None)

    if config_path is None:
        print('config-path is required!')
        raise SystemExit

    if artifact_path is None:
        print('artifact-path is required!')
        raise SystemExit

    if asset_name is None:
        print('name is required!')
        raise SystemExit

    # collect other inputs
    manufacturer = os.getenv('MANUFACTURER', '')
    model = os.getenv('MODEL', '')
    version = os.getenv('VERSION', '')
    
    print('OK!')
    print(f'Using "{config_path}",')
    print(f'Submitting "{artifact_path}"')
    print(f'As "{asset_name}"')
    print('Optional Inputs:')
    print(f'Manufacturer: "{manufacturer}"') if manufacturer else ''
    print(f'Model: "{model}"') if model else ''
    print(f'Version: "{version}"') if version else ''

    add_output('upload-id', 'abc')
    add_output('asset-id', 'def')
    add_output('uploaded', 'ghi')


if __name__ == '__main__':
    main()

