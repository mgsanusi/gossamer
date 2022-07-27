from gevent import monkey
monkey.patch_all()

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from cryptography.fernet import Fernet
from datetime import datetime, timedelta
from app.get_secrets import get_secret
from app.classes import EphemeralLoginData, PersistentLoginData

import pickle
import sqlalchemy
import zerorpc
import ast
import os
import zmq
from miscreant.aes.siv import SIV

from app import config
# from app import classes
# import sys
# sys.modules["app.classes"] = classes

#####################################################
create_new_database = False
use_rds_database = True

ephemeral_db_link = "mysql+mysqlconnector://{user}:{password}@{url}:{port}/{db_name}".format(**config.ephemeral_db)
engine = sqlalchemy.create_engine(ephemeral_db_link, echo=True, pool_recycle=500)
persistent_db_link = "mysql+mysqlconnector://{user}:{password}@{url}:{port}/{db_name}".format(**config.persistent_db)
rds_engine = sqlalchemy.create_engine(persistent_db_link, echo=True, pool_recycle=500)


print("Database connected")

base = declarative_base()
base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

if use_rds_database:
    RDS_DBSession = sessionmaker(bind=rds_engine)
    rds_session = RDS_DBSession()

# Generate the encryption key
key = Fernet.generate_key()
ephemeral_key = Fernet(key)
key_expiration = datetime.now() + timedelta(days=1)

persistent_key = get_secret("persistent_key").encode()
siv = SIV(persistent_key)
#####################################################

class EphemeralEntry(base):
    __tablename__ = "ephemeral_data"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    timestamp = sqlalchemy.Column(sqlalchemy.DateTime)
    username = sqlalchemy.Column(sqlalchemy.String(length=300))
    password = sqlalchemy.Column(sqlalchemy.String(length=300))
    ip = sqlalchemy.Column(sqlalchemy.String(length=300))
    header_json = sqlalchemy.Column(sqlalchemy.String(length=300))
    result = sqlalchemy.Column(sqlalchemy.Integer)

    def __repr__(self):
        return "<EphemeralEntry(username='{0}', password='{1}', ip='{2}', result='{3}', header_json='{4}')>".format(self.username, self.password, self.ip, self.result, self.header_json)

class PersistentEntry(base):
    __tablename__ = "persistent_data"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=False)
    timestamp = sqlalchemy.Column(sqlalchemy.DateTime)
    username = sqlalchemy.Column(sqlalchemy.PickleType)
    ip = sqlalchemy.Column(sqlalchemy.String(length=300))
    result = sqlalchemy.Column(sqlalchemy.Integer)
    header_json = sqlalchemy.Column(sqlalchemy.String(length=300))
    in_top_10_passwords = sqlalchemy.Column(sqlalchemy.Boolean)
    in_top_100_passwords = sqlalchemy.Column(sqlalchemy.Boolean)
    in_top_1000_passwords = sqlalchemy.Column(sqlalchemy.Boolean)
    appeared_in_breach = sqlalchemy.Column(sqlalchemy.Boolean)
    credential_tweaking_measurements = sqlalchemy.Column(sqlalchemy.PickleType)
    distance_from_submissions = sqlalchemy.Column(sqlalchemy.PickleType)
    frequently_submitted_password_today = sqlalchemy.Column(sqlalchemy.Boolean)
    frequently_submitted_username_today = sqlalchemy.Column(sqlalchemy.Boolean)
    zxcvbn_score = sqlalchemy.Column(sqlalchemy.Integer)
    zxcvbn_guesses = sqlalchemy.Column(sqlalchemy.Integer)
    in_top_2k_hashcat = sqlalchemy.Column(sqlalchemy.Boolean)
    in_top_5k_hashcat = sqlalchemy.Column(sqlalchemy.Boolean)
    in_top_2k_rockyou = sqlalchemy.Column(sqlalchemy.Boolean)
    in_top_5k_rockyou = sqlalchemy.Column(sqlalchemy.Boolean)

    def __repr__(self):
        return "<PersistentEntry ({})>".format(self.__dict__)

def encrypt_ephemeral(s):
    if s is None: return None
    return ephemeral_key.encrypt(s.encode()).decode()

def decrypt_ephemeral(s):
    if s is None: return None
    return ephemeral_key.decrypt(s.encode()).decode()

def encrypt_deterministically(s):
    ciphertext = siv.seal(s.encode())
    return ciphertext

def decrypt_deterministically(s):
    plaintext = siv.open(s)
    return plaintext.decode()

class DatabaseRPC(object):
    def store_ephemeral_entry(self, serialized_login_data):
        check_expiration()

        login_data = pickle.loads(serialized_login_data)
        print("Received request to store login data")
        entry = EphemeralEntry()
        entry.username = login_data.username
        entry.password = encrypt_ephemeral(login_data.password)
        entry.ip = encrypt_ephemeral(login_data.ip)
        entry.result = encrypt_ephemeral(str(login_data.result))
        entry.header_json = encrypt_ephemeral(login_data.header_json)
        # don't encrypt timestamp
        entry.timestamp = login_data.timestamp

        session.add(entry)
        try:
            session.commit()
        except:
            session.rollback()
            raise

        return int(entry.id)
    
    def retrieve_ephemeral_data_for_username(self, username):
        check_expiration()

        print("Received request to retrieve data")
        encrypted_data = session.query(EphemeralEntry).filter(EphemeralEntry.username == username).all()
        decrypted_data = [EphemeralLoginData(
            le.id,
            le.username,
            decrypt_ephemeral(le.password),
            decrypt_ephemeral(le.ip),
            decrypt_ephemeral(le.result),
            decrypt_ephemeral(le.header_json),
            le.timestamp
        ) for le in encrypted_data]

        result = pickle.dumps(decrypted_data)
        return result

    def store_persistent_entry(self, serialized_login_data):
        check_expiration()

        login_data = pickle.loads(serialized_login_data)
        print("Received request to store login data")
        entry = PersistentEntry()
        entry.id = login_data.id
        entry.username = encrypt_deterministically(login_data.username)
        entry.ip = login_data.ip
        entry.result = login_data.result
        entry.header_json = login_data.header_json
        entry.timestamp = login_data.timestamp
        entry.in_top_10_passwords = login_data.in_top_10_passwords
        entry.in_top_100_passwords = login_data.in_top_10_passwords
        entry.in_top_1000_passwords = login_data.in_top_1000_passwords
        entry.appeared_in_breach = login_data.appeared_in_breach
        entry.credential_tweaking_measurements = login_data.credential_tweaking_measurements
        entry.distance_from_submissions = login_data.distance_from_submissions
        entry.frequently_submitted_password_today = login_data.frequently_submitted_password_today
        entry.frequently_submitted_username_today = login_data.frequently_submitted_username_today
        entry.zxcvbn_score = login_data.zxcvbn_score
        entry.zxcvbn_guesses = login_data.zxcvbn_guesses
        entry.in_top_2k_hashcat = login_data.in_top_2k_hashcat
        entry.in_top_5k_hashcat = login_data.in_top_5k_hashcat
        entry.in_top_2k_rockyou = login_data.in_top_2k_rockyou
        entry.in_top_5k_rockyou = login_data.in_top_5k_rockyou

        if use_rds_database:
            rds_session.add(entry)
            try:
                rds_session.commit()
            except:
                rds_session.rollback()
                raise
        else:
            session.add(entry)
            try:
                session.commit()
            except:
                session.rollback()
                raise

        return "Successfully added persistent entry"

    def get_persistent_entry(self, id):
        entry = rds_session.query(PersistentEntry).filter(PersistentEntry.id == id).one() if use_rds_database \
                else session.query(PersistentEntry).filter(PersistentEntry.id == id).one()
        persistent_login_data = PersistentLoginData(
            entry.id,
            entry.username,
            entry.ip,
            entry.result,
            entry.header_json,
            entry.timestamp,
            entry.in_top_10_passwords,
            entry.in_top_100_passwords,
            entry.in_top_1000_passwords,
            entry.appeared_in_breach,
            entry.credential_tweaking_measurements,
            entry.distance_from_submissions,
            entry.frequently_submitted_password_today,
            entry.frequently_submitted_username_today,
            entry.zxcvbn_score,
            entry.zxcvbn_guesses,
            entry.in_top_2k_hashcat,
            entry.in_top_5k_hashcat,
            entry.in_top_2k_rockyou,
            entry.in_top_5k_rockyou
        )
        return pickle.dumps(persistent_login_data)

    def update_persistent_entry(self, id, serialized_credential_tweaking_measurements):
        entry = rds_session.query(PersistentEntry).filter(PersistentEntry.id == id).one() if use_rds_database \
                else session.query(PersistentEntry).filter(PersistentEntry.id == id).one()
        entry.credential_tweaking_measurements = pickle.loads(serialized_credential_tweaking_measurements)

        if use_rds_database:
            try:
                rds_session.commit()
            except:
                rds_session.rollback()
                raise
        else:
            try:
                session.commit()
            except:
                session.rollback()
                raise

        return "Successfully updated row"

def check_expiration():
    now = datetime.now()
    if now > key_expiration:
        clear_ephemeral_db()
        generate_new_key(now)
        

def generate_new_key(now):
    global key
    global f
    global key_expiration
    key = Fernet.generate_key()
    f = Fernet(key)
    key_expiration = now + timedelta(days=1)

def clear_ephemeral_db():
    deleted = session.query(EphemeralEntry).delete()

    try:
        session.commit()
    except:
        session.rollback()
        raise

    print("Deleted " + str(deleted) + " rows")

#####################################################
# Start up the ZeroRPC server
if __name__ == "__main__":
    if create_new_database:
       base.metadata.create_all()

    # Clear the database. Anything currently in there was encrypted with a previous key.
    clear_ephemeral_db()

    s = zerorpc.Server(DatabaseRPC(), heartbeat=None)
    db_socket_path = "/tmp/db_sock__"
    s.bind("ipc://{}".format(db_socket_path))
    print("Ready")
    s.run()
