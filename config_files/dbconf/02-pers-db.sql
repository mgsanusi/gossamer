# create databases
CREATE DATABASE IF NOT EXISTS `sso`;

# create root user and grant rights
CREATE USER 'admin'@'localhost' IDENTIFIED BY 'changeme';
GRANT ALL PRIVILEGES ON *.* TO 'admin'@'%';

# create table
CREATE TABLE `measurements` (
  `id` bigint(20) unsigned NOT NULL,
  `timestamp` datetime DEFAULT NULL,
  `timestamp_received` datetime(3) DEFAULT NULL,
  `username` varchar(300) DEFAULT NULL,
  `ip` varchar(300) DEFAULT NULL,
  `result` tinyint(1) DEFAULT NULL,
  `result_code` int(11) DEFAULT NULL,
  `header_json` varchar(5000) DEFAULT NULL,
  `in_top_10_passwords` tinyint(1) DEFAULT NULL,
  `in_top_100_passwords` tinyint(1) DEFAULT NULL,
  `in_top_1000_passwords` tinyint(1) DEFAULT NULL,
  `appeared_in_breach` tinyint(1) DEFAULT NULL,
  `username_appeared_in_breach` tinyint(1) DEFAULT NULL,
  `password_appeared_in_breach` tinyint(1) DEFAULT NULL,
  `credential_tweaking_measurements` blob,
  `distance_from_submissions_by_username` blob,
  `distance_from_submissions_by_ip` blob,
  `frequently_submitted_password_today` tinyint(1) DEFAULT NULL,
  `frequently_submitted_username_today` tinyint(1) DEFAULT NULL,
  `zxcvbn_score` int(11) DEFAULT NULL,
  `in_top_2k_hashcat` tinyint(1) DEFAULT NULL,
  `in_top_5k_hashcat` tinyint(1) DEFAULT NULL,
  `in_top_2k_rockyou` tinyint(1) DEFAULT NULL,
  `in_top_5k_rockyou` tinyint(1) DEFAULT NULL,
  `malformed_password` tinyint(1) DEFAULT NULL,
  `compilation_tags` varchar(500) DEFAULT NULL,
  `user_agent` varchar(500) DEFAULT NULL,
  `unique_passwords_by_username` int(11) DEFAULT NULL,
  `unique_passwords_by_ip` int(11) DEFAULT NULL,
  `credential_tweaking_measurements_json` json DEFAULT NULL,
  `distance_from_submissions_by_username_json` json DEFAULT NULL,
  `distance_from_submissions_by_ip_json` json DEFAULT NULL,
  `tweaked` tinyint(1) DEFAULT NULL,
  `is_unique_pws_by_ip` tinyint(1) DEFAULT NULL,
  `typo` tinyint(1) DEFAULT NULL,
  `edit_distance` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`),
  KEY `ip` (`ip`),
  KEY `timestamp` (`timestamp`),
  KEY `username` (`username`)
);
