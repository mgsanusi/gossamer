# create databases
CREATE DATABASE IF NOT EXISTS `eph`;

# create root user and grant rights
CREATE USER 'sso'@'localhost' IDENTIFIED BY 'changeme';
GRANT ALL PRIVILEGES ON *.* TO 'sso'@'%';

# CREATE TABLE ABCD;
