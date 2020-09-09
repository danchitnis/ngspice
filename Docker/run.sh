#!/bin/bash
echo Entryponit script is Running...
echo

users=$(($#/3))
mod=$(($# % 3))

echo "users is $users"
echo "mod is $mod"

if [[ $# -eq 0 ]]; then 
    echo "No input parameters. exiting..."
    echo "there should be 3 input parameters per user"
    exit
fi

if [[ $mod -ne 1 ]]; then 
    echo "incorrect input. exiting..."
    echo "there should be 1 input parameters per user"
    exit
fi
echo "You entered $users users"


    #echo "username is $1"
    #useradd $1
    #wait
    #getent passwd | grep foo
    echo foo:$1 | chpasswd 
    wait
    #echo "sudo is $3"
   
    #usermod -aG wheel foo
   
    wait
    echo "user '$1' is added"




echo -e "This script is ended\n"

echo -e "starting xrdp services...\n"
xrdp-sesman && xrdp -n 



