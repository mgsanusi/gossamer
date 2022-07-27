#!/bin/bash

cd /var/www/gossamer/

### Copy over credtweak models. Replace line with wherever your credtweak models are stored.
# aws s3 cp --recursive s3://gossamer-credtweak-models/ ./credtweak_models/

source bin/activate
