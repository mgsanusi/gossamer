import decimal
import pickle
import pytest
from inspect import getsourcefile
import os.path
import sys

from app import heuristic_worker
from app.heuristic_worker import parse_breach_data
from app.classes import EphemeralLoginData

p1 = "password1111"
p2 = "password2222"
p3 = "password3333"
p4 = "password4444"

heuristic_worker.breach_dict = {"brayden" : ["password123", "super_secure_pwd"], "eliza" : ["myspecialpassword"]}

def test_parse_breach_data():
    heuristic_worker.cornell_breach_fname = "/var/www/gossamer/tests/test_breach_data.txt"
    breach_pairs, breach_dict = parse_breach_data()
    assert(isinstance(breach_pairs, list))
    assert(isinstance(breach_dict, dict))
    assert(len(breach_pairs) == 6)
    assert(len(breach_dict.keys()) == 3)
    assert(breach_pairs[0][0] == "rrobert")
    assert(len(breach_dict["rrobert"]) == 3)

def test_add_to_bloom_filter():
    # Only stash the top 3 most frequent passwords for easy testing
    heuristic_worker.N = 3

    # Not in the stash; Haven't filled up the stash yet; Should be added to it
    heuristic_worker.add_to_bloom_filter(p1, heuristic_worker.password_bloom, heuristic_worker.password_stash)
    assert(p1 in heuristic_worker.password_bloom)
    assert(p1 in heuristic_worker.password_stash)

    heuristic_worker.add_to_bloom_filter(p2, heuristic_worker.password_bloom, heuristic_worker.password_stash)
    assert(p2 in heuristic_worker.password_bloom)
    assert(p2 in heuristic_worker.password_stash)

    # Already in the stash; Should add again to bloom filter and increase frequency
    heuristic_worker.add_to_bloom_filter(p1, heuristic_worker.password_bloom, heuristic_worker.password_stash)
    assert(heuristic_worker.password_bloom.check(p1) <= 2)
    assert(heuristic_worker.password_stash[p1] == 2)

    # Fill up the stash now
    heuristic_worker.add_to_bloom_filter(p1, heuristic_worker.password_bloom, heuristic_worker.password_stash)
    heuristic_worker.add_to_bloom_filter(p2, heuristic_worker.password_bloom, heuristic_worker.password_stash)
    heuristic_worker.add_to_bloom_filter(p3, heuristic_worker.password_bloom, heuristic_worker.password_stash)

    # Not in the stash, stash is full, doesn't make it in
    heuristic_worker.add_to_bloom_filter(p4, heuristic_worker.password_bloom, heuristic_worker.password_stash)
    assert(p4 in heuristic_worker.password_bloom)
    assert(not p4 in heuristic_worker.password_stash)

    # Not in the stash, stash is full, makes it in
    heuristic_worker.add_to_bloom_filter(p4, heuristic_worker.password_bloom, heuristic_worker.password_stash)
    assert(p4 in heuristic_worker.password_bloom)
    assert(p4 in heuristic_worker.password_stash)

def test_frequently_submitted_password_today():
    assert(heuristic_worker.frequently_submitted_password_today(p1) == True)
    assert(heuristic_worker.frequently_submitted_password_today(p3) == False) # Password submitted but not frequent
    assert(heuristic_worker.frequently_submitted_password_today("password_never_submitted") == False)

def test_appeared_in_breach():
    assert(heuristic_worker.appeared_in_breach("brayden", "password123") == True)
    assert(heuristic_worker.appeared_in_breach("brayden", "password_not_in_breach") == False)
    assert(heuristic_worker.appeared_in_breach("tom", "super_secure_pwd") == False)

# TODO: Figure out how to mock things to implement this
def test_credential_tweaking_measurements():
    pass

def test_distance_from_submissions(mocker):
    mock_ret_val = pickle.dumps([EphemeralLoginData(6, "user", p, "ip", False, "welrkj", None) for p in ["mypassword", "password123", "p4ssw0rd"]])
    mocker.patch("app.heuristic_worker.db_c.retrieve_ephemeral_data_for_username", return_value=mock_ret_val)
    result = heuristic_worker.distance_from_submissions(5, "user", "password")
    assert(len(result) == 3)
    assert(result == [2, 3, 2])

def test_in_top_10_passwords():
    assert(heuristic_worker.in_top_10_passwords("password") == True)
    assert(heuristic_worker.in_top_10_passwords("jalsfkj13lkfj320843jlk1$L#!K$J#$LK^J") == False)

def test_in_top_100_passwords():
    assert(heuristic_worker.in_top_100_passwords("computer") == True)
    assert(heuristic_worker.in_top_100_passwords("jalsfkj13lkfj320843jlk1$L#!K$J#$LK^J") == False)

def test_in_top_1000_passwords():
    assert(heuristic_worker.in_top_1000_passwords("bubbles") == True)
    assert(heuristic_worker.in_top_1000_passwords("jalsfkj13lkfj320843jlk1$L#!K$J#$LK^J") == False)

## TODO: Uncomment/update once we implement zxcvbn bucketization
##def test_get_zxcvbn_results():
#    # Mostly just to test the API
#    #score, guesses = heuristic_worker.get_zxcvbn_results("password123") 
#    #assert(isinstance(score, int))
#    #assert(isinstance(guesses, decimal.Decimal))
#
def test_in_top_2k_hashcat():
    assert(heuristic_worker.in_top_2k_hashcat_passwords("123456") == True)
    assert(heuristic_worker.in_top_2k_hashcat_passwords("samaha") == False)
    assert(heuristic_worker.in_top_2k_hashcat_passwords("jawkefjlksdflsfkj13lkfj320843jlk1$L#!K$J#$LK^J") == False)

def test_in_top_5k_hashcat():
    assert(heuristic_worker.in_top_5k_hashcat_passwords("123456") == True)
    assert(heuristic_worker.in_top_5k_hashcat_passwords("samaha") == True)
    assert(heuristic_worker.in_top_5k_hashcat_passwords("jawkefjlksdflsfkj13lkfj320843jlk1$L#!K$J#$LK^J") == False)

def test_in_top_2k_rockyou():
    assert(heuristic_worker.in_top_2k_rockyou_passwords("123456") == True)
    assert(heuristic_worker.in_top_2k_rockyou_passwords("speaker") == False)
    assert(heuristic_worker.in_top_2k_rockyou_passwords("jawkefjlksdflsfkj13lkfj320843jlk1$L#!K$J#$LK^J") == False)

def test_in_top_5k_rockyou():
    assert(heuristic_worker.in_top_5k_rockyou_passwords("123456") == True)
    assert(heuristic_worker.in_top_5k_rockyou_passwords("speaker") == True)
    assert(heuristic_worker.in_top_5k_rockyou_passwords("jawkefjlksdflsfkj13lkfj320843jlk1$L#!K$J#$LK^J") == False)
