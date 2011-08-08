#!/bin/bash

set -o errexit

gnome-terminal --title=appengine -e \
    "/bin/bash -c '~/google_appengine/dev_appserver.py --port 8888\
    src/appengine;\
    read -p \"press enter to exit\"'"
gnome-terminal --title=ldapserver -e \
    "/bin/bash -c './run_remote_server.sh;\
    read -p \"press enter to exit\"'"
src/swipeup.py

