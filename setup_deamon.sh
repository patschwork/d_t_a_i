#!/bin/sh

pyexec=$(which python)
currentdir=$(pwd)
scripttocopy="d_t_a_i_daemon.sh"
etcinitd="/etc/init.d/"


error() {
  printf '\E[31m'; echo "$@"; printf '\E[0m'
}

#if [ $EUID -ne 0 ];
#    then error "This script should be run using sudo or as the root user"
#    exit 1
#fi

#isroot=$(whoami)

#if [ $EUID = "0" ]; then
#	error "run as root or with sudo"
#	exit 1
#fi


echo "copy $scripttocopy to $etcinitd as root or with sudo"
echo ""

echo "Change settings in $etcinitd$scripttocopy to"
echo "dir=""$currentdir"""
echo "cmd=""$pyexec $etcinitd/start.py <folder where to find file_to_observe.json>"""

echo ""
echo "Then run: sudo update-rc.d $scripttocopy defaults"
