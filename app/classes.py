class EphemeralLoginData():
    def __init__(self, id, username, password, ip, result, header_json, timestamp):
        self.id = id
        self.username = username
        self.password = password
        self.ip = ip
        self.result = result
        self.header_json = header_json
        self.timestamp = timestamp

class PersistentLoginData():
    def __init__(
        self,
        id,
        username,
        ip,
        result,
        header_json,
        timestamp,
        in_top_10_passwords,
        in_top_100_passwords,
        in_top_1000_passwords,
        appeared_in_breach,
        credential_tweaking_measurements,
        distance_from_submissions,
        frequently_submitted_password_today,
        frequently_submitted_username_today,
        zxcvbn_score,
        zxcvbn_guesses,
        in_top_2k_hashcat,
        in_top_5k_hashcat,
        in_top_2k_rockyou,
        in_top_5k_rockyou
    ):
        self.id = id
        self.username = username
        self.ip = ip
        self.result = result
        self.header_json = header_json
        self.timestamp = timestamp
        self.in_top_10_passwords = in_top_10_passwords
        self.in_top_100_passwords = in_top_100_passwords
        self.in_top_1000_passwords = in_top_1000_passwords
        self.appeared_in_breach = appeared_in_breach
        self.credential_tweaking_measurements = credential_tweaking_measurements
        self.distance_from_submissions = distance_from_submissions
        self.frequently_submitted_password_today = frequently_submitted_password_today
        self.frequently_submitted_username_today = frequently_submitted_username_today
        self.zxcvbn_score = zxcvbn_score
        self.zxcvbn_guesses = zxcvbn_guesses
        self.in_top_2k_hashcat = in_top_2k_hashcat
        self.in_top_5k_hashcat = in_top_5k_hashcat
        self.in_top_2k_rockyou = in_top_2k_rockyou
        self.in_top_5k_rockyou = in_top_5k_rockyou
