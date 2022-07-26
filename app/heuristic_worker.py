from gevent import monkey
monkey.patch_all()

import zmq
import shelve
import pickle
import zerorpc
import editdistance
from zxcvbn import zxcvbn
from probables import CountingBloomFilter
from pathlib import Path

from app.classes import EphemeralLoginData, PersistentLoginData
# import classes
# import sys
# sys.modules["app.classes"] = classes
from app.credtweak_models.ppsm import ppsm
import os


# Connect client for communicating with db
db_c = zerorpc.Client(heartbeat=None)
db_socket_path = "/tmp/db_sock__"
db_c.connect("ipc://{}".format(db_socket_path))

password_bloom = CountingBloomFilter(est_elements=10000, false_positive_rate=0.01)
username_bloom = CountingBloomFilter(est_elements=10000, false_positive_rate=0.01)
password_stash = {} # Store top N most common passwords
username_stash = {} # Store top N most common passwords
threshold = 0 # The frequency of the least common element in the stash
N = 50

APP_DIR = Path(os.path.dirname(os.path.realpath(__file__)))
#APP_DIR = Path("/var/www/gossamer/app/")
DATA_DIR = APP_DIR / "data"
pass2path_shelve = shelve.open(str(APP_DIR / "credtweak_models/pass2path.shelve"))

breach_fname = str(DATA_DIR / "breach.txt") # Replace with your organization's breached username-password pairs
top_1000_fname = str(DATA_DIR / "top_1000_passwords.txt") # Top 1k pwds in our entire Breach Compilation
hashcat_5k_fname = str(DATA_DIR / "hashcat_5000.txt") # First 5k pwds generated by Hashcat using Best64.rule
rockyou_5k_fname = str(DATA_DIR / "rockyou_5000.txt") # Top 5k pwds found in the RockYou breach

with open(top_1000_fname, "r") as f:
    content = f.read().split("\n")
    top_1000 = [line.split()[1] if len(line.split()) >= 2 else "" for line in content]
    top_100 = set(top_1000[:100])
    top_10 = set(top_1000[:10])
    top_1000 = set(top_1000)

with open(hashcat_5k_fname, "r") as f:
    content = f.read().split("\n")
    lines = [line.strip() for line in content]
    hashcat_2k = set(lines[:2000])
    hashcat_5k = set(lines)

with open(rockyou_5k_fname, "r") as f:
    content = f.read().split("\n")
    lines = [line.strip() for line in content]
    rockyou_2k = set(lines[:2000])
    rockyou_5k = set(lines)

def parse_breach_data():
    with open(breach_fname, "r") as f:
        lines = f.read().split("\n") 
        breach_pairs = []
        for line in lines:
            split_line = line.split(":")
            if len(split_line) == 2:
                breach_pairs.append((split_line[0], split_line[1]))

        breach_dict = {}
        for breach_pair in breach_pairs:
            username = breach_pair[0]
            if username in breach_dict:
                breach_dict[username].append(breach_pair[1])
            else:
                breach_dict[username] = [breach_pair[1]]
    return breach_dict

# breach_dict: username -> list of breached passwords
breach_dict = parse_breach_data()

def process_request(login_data):
    if login_data.result != 0: # If login was unsuccessful
        add_to_bloom_filter(login_data.password, password_bloom, password_stash)
    add_to_bloom_filter(login_data.username, username_bloom, username_stash)
    id = db_c.store_ephemeral_entry(pickle.dumps(login_data))
    get_heuristics(login_data, id)
    return "success"

def add_to_bloom_filter(value, bloom_filter, stash):
    count = bloom_filter.add(value)

    if value in stash:
        stash[value] += 1
    elif len(stash) < N: # We haven't filled up the stash yet
        stash[value] = 1
    else: 
        min_key = min(stash.keys(), key=(lambda k: stash[k]))
        min_val = stash[min_key]
        
        if bloom_filter.check(value) > min_val:
            stash[value] = count
            stash.pop(min_key)

def get_heuristics(login_data, id):
    print("Received request to get heuristics")
    username = login_data.username
    password = login_data.password
    zxcvbn_score, zxcvbn_guesses = get_zxcvbn_results(password)

    entry = PersistentLoginData(
        id,
        login_data.username,
        login_data.ip,
        login_data.result,
        login_data.header_json,
        login_data.timestamp,
        in_top_10_passwords(password),
        in_top_100_passwords(password),
        in_top_1000_passwords(password),
        appeared_in_breach(username, password),
        get_credential_tweaking_measurements(id, username, password, login_data.result),
        distance_from_submissions(id, username, password),
        frequently_submitted_password_today(password),
        frequently_submitted_username_today(username),
        zxcvbn_score,
        zxcvbn_guesses,
        in_top_2k_hashcat_passwords(password),
        in_top_5k_hashcat_passwords(password),
        in_top_2k_rockyou_passwords(password),
        in_top_5k_rockyou_passwords(password)
    )

    print("Sending to database accessor to be stored...")
    db_c.store_persistent_entry(pickle.dumps(entry))
    return "Successfully calculated and stored heuristics"

# How far away from previous breached passwords for this username is this password?
# Returns: array of measurements where one dimension is the breached passwords and actual password (back-populated), and the other dimension
# is three password similarity measurements--edit distance, PPSM score, and Pass2path guess rank.
def get_credential_tweaking_measurements(id, username, password, result):
    breached_passwords = breach_dict[username] if username in breach_dict else []
    # Initialize empty measurement array
    measurements = [[None for _ in range(3)] for _ in range(len(breached_passwords)+1)]
    i = 1
    for bp in breached_passwords:
        # calculate edit distance
        edit_distance = editdistance.eval(password, bp)
        # calculate ppsm
        ppsm_result = ppsm(bp, password)
        # calculate pass2path
        rank = pass2path_shelve[bp].index(password) if (bp in pass2path_shelve and password in pass2path_shelve[bp]) else None

        measurements[i][0] = edit_distance
        measurements[i][1] = ppsm_result
        measurements[i][2] = rank
        i += 1

    if result == 0: # If login was successful
        entries = pickle.loads(db_c.retrieve_ephemeral_data_for_username(username)) # get all the ephemeral entries for this username
        for entry in entries:
            if entry.id == id:
                continue
            # calculate edit distance and ppsm
            persistent_entry = pickle.loads(db_c.get_persistent_entry(entry.id))
            new_measurements = persistent_entry.credential_tweaking_measurements

            edit_distance = editdistance.eval(password, entry.password)
            ppsm_result = ppsm(password, entry.password)

            new_measurements[0][0] = edit_distance
            new_measurements[0][1] = ppsm_result
            # write to db
            db_c.update_persistent_entry(entry.id, pickle.dumps(new_measurements))
    # return measurements to write to db
    return measurements

# Is this password one of the top N most incorrect, submitted passwords stored in ephemeral data?
# Returns: bool
def frequently_submitted_password_today(password):
    return password in password_stash and password_stash[password] > 1 # If the frequency == 1, we're probably still populating the stash

# Is this username one of the top N most submitted passwords stored in ephemeral data?
# Returns: bool
def frequently_submitted_username_today(username):
    return username in username_stash and username_stash[username] > 1 # If the frequency == 1, we're probably still populating the stash

# Did this username-password pair appear in a breach?
# Returns: bool
def appeared_in_breach(username, password):
   return username in breach_dict and password in breach_dict[username] 

# How far away from previous submissions for this user is the password?
# Returns: vector<int> (edit distance from the past n passwords)
def distance_from_submissions(id, username, password):
    print("Sending request to retrieve ephemeral data...")
    result = db_c.retrieve_ephemeral_data_for_username(username)
    past_submissions = pickle.loads(result)
    return [editdistance.eval(password, s.password) for s in past_submissions if s.id != id]

# Is this in the top 10 most common breached passwords?
# Returns: bool
def in_top_10_passwords(password):
    return password in top_10

# Is this in the top 100 most common breached passwords?
# Returns: bool
def in_top_100_passwords(password):
    return password in top_100

# Is this in the top 1000 most common breached passwords?
# Returns: bool
def in_top_1000_passwords(password):
    return password in top_1000

# Is this in the first 2k Hashcat passwords?
# Returns: bool
def in_top_2k_hashcat_passwords(password):
    return password in hashcat_2k

# Is this in the first 5k Hashcat passwords?
# Returns: bool
def in_top_5k_hashcat_passwords(password):
    return password in hashcat_5k

# Is this in the top 2k RockYou passwords?
# Returns: bool
def in_top_2k_rockyou_passwords(password):
    return password in rockyou_2k

# Is this in the top 5k RockYou passwords?
# Returns: bool
def in_top_5k_rockyou_passwords(password):
    return password in rockyou_5k

# How strong is this password according to zxcvbn?
# Returns: (int, int) -  score on scale of 1-10, estimated number of guesses till password cracked
def get_zxcvbn_results(password):
    result = zxcvbn(password)
    return result["score"], result["guesses_log10"]

if __name__ == "__main__":
    context = zmq.Context()
    socket = context.socket(zmq.PULL)
    socket.connect("tcp://127.0.0.1:5560")
    print("Ready")

    while True:
        print("Listening for message...")
        payload = socket.recv_pyobj()
        print("Received message")
        process_request(payload)
