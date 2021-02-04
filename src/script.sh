#! /bin/bash

a_flag=''
b_flag=''
files=''
verbose='false'

print_usage() {
    echo "$package - parser for C programs"
    echo " "
    echo "$package [options] application [arguments]"
    echo " "
    echo "options:"
    echo "-h, --help                show brief help"
    echo "-o, --output-dir=DIR      specify a directory to store output in"
    echo "-v, --action=ACTION       specify an action to use"
}

while getopts 'abf:v' flag; do
  case "${flag}" in
    a) a_flag='true' ;;
    b) b_flag='true' ;;
    f) files="${OPTARG}" ;;
    v) verbose='true' ;;
    *) print_usage
       exit 1 ;;
  esac
done