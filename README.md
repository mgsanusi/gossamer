# gossamer

## Setup
1. Clone this repository in the `/var/www` directory.  
2. Set the variables marked CHANGEME in `app/get_secrets.py`, `config_files/environment_vars`, `config_files/dbconf/01-eph-db.sql`, `config_files/dbconf/02-pers-db.sql`, `app/config.py`, and `docker-compose.yml`.
3. Add breached username-password pairs for your organization in `app/data/breach.txt`.
3. Compute the password similarity predictions for your organization following the instructions [in the credtweak repo (Pal et al. 2019)](https://github.com/Bijeeta/credtweak), and place the resulting `.predictions` file in the `app/credtweak_models` folder. (The models we used to generate the predictions in our paper can be found [here](https://gossamer-credtweak-models.s3.amazonaws.com/models.zip)).
4. Run the following lines to parse the predictions into a shelve data structure.
```
    cd app/credtweak_models
    python3 create_shelve.py
    cd ../..
```
5. The `app/get_secrets.py` file expects a secrets file at the location `/var/lib/sso-secrets/secrets.conf` (that is copied to `/var/run/secrets` at runtime). This can be changed depending on your organization's security preferences (for example, you could instead use AWS secrets manager). If using the `secrets.conf` file, though, copy the `secrets.conf` file in the repo to `/var/lib/sso-secrets/`, and set the CHANGEME variables.
6. Set up TLS Mutual Authentication by following [the instructions here](https://www.openlogic.com/blog/mutual-authentication-using-apache-and-web-client) The SSL config for the dev VM is located at `/etc/httpd/conf.d/ssl.conf`, and the certs are located in `/etc/ssl/private` and `/etc/ssl/certs`.
7. Install Docker

To build the docker image:
```bash
$ make build
$ make run

## To log into the container
$ docker exec -it gossamer_web_1 bash   # or
$ docker exec -it gossamer_ephdb_1 bash
```

## Testing
Unit tests in the `tests` directory can be run using the `pytest tests` command in the repo home directory.
