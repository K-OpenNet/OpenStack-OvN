#!/usr/bin/env bash

if [ `id -u` -ne 0 ]; then
    echo "You require ROOT PERMISSION to execute it"
    exit
fi

apt update
apt install -y python python-pip
pip install PyYaml simplejson httplib2