import boto3
import base64
from botocore.exceptions import ClientError
import ast
import os, sys
from pathlib import Path
import six.moves.configparser
import hashlib

build = os.environ.get('BUILD')

SEC_LOC = Path('/var/run/secrets/')
SEC_FILE = SEC_LOC / 'secrets.conf'

config = six.moves.configparser.ConfigParser()
def read_secret_config(section, config_file=SEC_FILE):
    assert config_file.exists(), f"{config_file!r} does not exist"
    try:
        with config_file.open() as f:
            pass
    except Exception as ex:
        print(f"{config_file!r} cannot be read by '{os.getuid()}'. Exception: {ex!r}")
        raise ex

    config.read(config_file)
    return dict(config.items(section))

def get_secret(key):
    """Retrieve the secrets from some path"""
    config_d = read_secret_config('defaults')
    if build == "test":
        return "testsecret"
    else:
        return get_secret_key(key).encode() if key == "persistent_key" else get_secret_key(key)

def get_secret_key(key):
    c = read_secret_config('defaults')
    try:
        return c[key]
    except KeyError as ex:
        print("No key for {!r} at {}".format(key, SEC_LOC))
        raise(ex)


# OPTIONAL AWS SECRETS MANAGER ALTERNATIVE FOR GETTING SECRETS
aws_secrets_config = dict(
    dev = { 
            "secret_name" : "changeme",
            "region_name" : "changeme",
            "key_name" : "changeme"
        },  
    prod = { 
            "secret_name" : "changeme",
            "region_name" : "changeme",
            "key_name" : "changeme"
        }   
)[build]

def get_aws_secret():
    secret_name = aws_secrets_config["secret_name"]
    region_name = aws_secrets_config["region_name"]
    key_name = aws_secrets_config["key_name"]

    session = boto3.session.Session()
    client = session.client(
        service_name="secretsmanager",
        region_name=region_name
    )   

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )   
    except ClientError as e:
        raise e
    else:
        secret = ast.literal_eval(get_secret_value_response['changeme'])[key_name]
        hash_ = hashlib.sha1(secret.encode()).hexdigest()[:32]
        return hash_.encode()

if __name__ == "__main__":
    import sys
