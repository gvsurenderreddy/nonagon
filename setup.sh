#!/bin/bash
. nonagon.env
mkdir /etc/nonagon
cp nonagon.env /etc/nonagon/
cp interfaces.conf /etc/nonagon/
mkdir -p $NFLOWLIST
cp 90-nonagon-init /etc/sudoers.d/
adduser --disabled-password --gecos '' --conf adduser.conf --home /usr/lib/nonagon nonagon
chown -R nonagon:nonagon /etc/nonagon
chown -R nonagon:nonagon /var/lib/nonagon
