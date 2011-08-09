#!/bin/bash
set -o errexit

CS_USERNAME='henninl8' # Put your cs username here
CS_MACHINE='eng007'
# Option for cmdline argument for name
if [[ -n "${1}" ]] ; then
    CS_USERNAME="${1}"
fi

echo "starting ssh tunnel for $CS_USERNAME"
SSH="ssh -N -L 8000:edir.man.ac.uk:389 -L 8001:ldap.man.ac.uk:389 $CS_USERNAME@$CS_MACHINE.cs.man.ac.uk"
eval ${SSH} &

src/swipeup.py -l localhost -p 8000

SSH_PID=`ps ax | grep -e "${SSH}" | grep -v grep | awk '{print $1}'`
kill $SSH_PID

