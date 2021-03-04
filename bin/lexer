#! /bin/bash

outfile=''
o_flag=false
verbose=false
package=$0
# package='lexer'
pyscript="`dirname $(realpath $0)`/../src/lexer.py"

print_usage() {
    echo "USAGE: $package [options] file..."
    echo "Try \`$package --help\` for more informations."
    exit 1
}

display_help() {
    echo "$package - token scanner for C programs"
    echo "USAGE:  $package [options] file..."
    echo " "
    echo "options:"
    echo "  -h, --help             shows brief help"
    echo "  -o, --output=FILE      specify a file to store output"
    echo "  -v, --verbose          force output on stdout"
    exit 0
}

options=$(getopt -l "help,verbose,output-dir:" -o "hvo:" -- "$@")
if [ $? != 0 ] ; then print_usage; fi

eval set -- "$options"

while true ; do
    case "$1" in
        -h|--help) 
          display_help 
          ;;
        -v|--verbose)
          verbose=true
          shift 1 
          ;;
        -o|--output-dir)
          o_flag=true
          outfile=$2
          shift 2 
          ;;
        --) 
          shift
          break 
          ;;
        *) print_usage ;;
    esac
done

if [ "$1" != "" ] && [[ -e "$PWD/$1" ]]; then
  if [ "$o_flag" == true ]; then
      if [[ "$outfile" == "" ]]; then
        echo "$package: Invalid output file"
        echo "Try \`$package --help\` for more informations."
        exit 1
      fi
      python3 $pyscript $1 >| $outfile
      if [ "$verbose" == true ]; then cat $outfile; fi
  else
    python3 $pyscript $1
  fi
elif [ "$1" != "" ]; then
  echo "$package: \`$1\`: No such file exists"
  echo "Try \`$package --help\` for more informations."
  exit 1
else
  print_usage
fi
