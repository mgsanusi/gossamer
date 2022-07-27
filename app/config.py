import os
from app.get_secrets import get_secret
from pathlib import Path

ephemeral_db = {
    'user': 'sso',
    'password': 'changeme',
    'url': 'ephdb',
    'port': 3306,
    'db_name': 'eph'
}

persistent_db = {
    'user': 'admin',
    'password': get_secret("persist_db_pw"),
    'url': "ephdb",
    'port': 3306,
    'db_name': 'prst'
}
