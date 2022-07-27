from inspect import getsourcefile
from alchemy_mock.mocking import UnifiedAlchemyMagicMock
import os.path
import sys
import pytest
import pickle

# current_path = os.path.abspath(getsourcefile(lambda:0))
# current_dir = os.path.dirname(current_path)
# parent_dir = current_dir[:current_dir.rfind(os.path.sep)]

# sys.path.insert(0, parent_dir)

from app.database_accessor import (
    encrypt_ephemeral,
    decrypt_ephemeral, encrypt_deterministically,
    decrypt_deterministically, session,
    DatabaseRPC, EphemeralEntry, PersistentEntry
)
from app import database_accessor
from app.classes import EphemeralLoginData, PersistentLoginData

db_rpc = DatabaseRPC()

def test_encrypt_decrypt():
    s = "this_is_a_secret_string_to_encrypt"
    encrypted_string = encrypt_ephemeral(s)
    decrypted_string = decrypt_ephemeral(encrypted_string)
    assert(s == decrypted_string)

def test_encrypt_decrypt_deterministically():
    s = "secret_secret_string_that_is_longer_than_16_bytes"
    encrypted_string = encrypt_deterministically(s)
    decrypted_string = decrypt_deterministically(encrypted_string)
    assert(s == decrypted_string)

def test_retrieve_ephemeral_data_for_username(mocker):
    entry = EphemeralEntry()
    entry.id = 4
    entry.username = "user123"
    entry.password = encrypt_ephemeral("pass123")
    entry.ip = encrypt_ephemeral("0.00.0.0")
    entry.header_json = encrypt_ephemeral("lwkefjwe")
    
    database_accessor.session = UnifiedAlchemyMagicMock(data=[
        (
            [mocker.call.query(EphemeralEntry), mocker.call.filter(EphemeralEntry.username == "user123")],
            [entry]
        )
    ])
    result = db_rpc.retrieve_ephemeral_data_for_username("user123")
    unpickled_result = pickle.loads(result)
    assert(len(unpickled_result) == 1)
    assert(unpickled_result[0].username == "user123")
    assert(unpickled_result[0].password == "pass123")

def test_store_persistent_entry(mocker):
    database_accessor.rds_session = UnifiedAlchemyMagicMock()
    database_accessor.use_rds_database = True
    param = PersistentLoginData(
        5,
        "username",
        "123.456.789.5",
        5511,
        "headers",
        None,
        False,
        True,
        True,
        True,
        [[1, 2, 3], [4, 5, 6]],
        [1, 2],
        False,
        True,
        4,
        6,
        False,
        False,
        True,
        True)
    db_rpc.store_persistent_entry(pickle.dumps(param))
    database_accessor.rds_session.add.assert_called_once()
    database_accessor.rds_session.commit.assert_called_once()

def test_get_persistent_entry(mocker):
    entry = PersistentEntry()
    entry.username = "encrypted_username"
    entry.header_json = "lwkefjwe"
    entry.in_top_10_passwords = True
    database_accessor.use_rds_database = True
    database_accessor.rds_session = UnifiedAlchemyMagicMock(data=[
        (
            [mocker.call.query(PersistentEntry), mocker.call.filter(PersistentEntry.id == 2)],
            [entry]
        )
    ])

    result = db_rpc.get_persistent_entry(2)
    unpickled_result = pickle.loads(result)
    assert(unpickled_result is not None)
    assert(unpickled_result.username == "encrypted_username")
