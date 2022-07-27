# create databases
CREATE DATABASE IF NOT EXISTS `sso`;

# create root user and grant rights
CREATE USER 'test'@'localhost' IDENTIFIED BY 'changeme';
GRANT ALL PRIVILEGES ON *.* TO 'test'@'%';

# CREATE TABLE ABCD;
