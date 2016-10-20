#!/usr/bin/env bash
set -e
if [ "$1" == "-h" ]; then
    echo "usage: $0 MASTERCONF OPALDIR TARBALL [clone]"
    exit 1
fi

MASTERCONF="./master_conf.json"
OPALDIR="opals-sources"
TARBALL="opals.tar.gz"
CLONE="clone"

MASTERCONF=${1:-MASTERCONF}
OPALDIR=${2:-"opals-sources"}
TARBALL=${3:-"opals.tar.gz"}
CLONE=${4:-"clone"}
mkdir -p "$OPALDIR"
if [ $? -ne 0 ]; then
    echo "FATA: could not make OPALDIR $OPALDIR"
fi

if [ ! -z $CLONE ]; then
    repos=$(jq -r 'to_entries
                  | .[]
                  | ["git@"+.value.host + ":" + .value.repo, .key ]
                  | @sh ' < "$MASTERCONF")
else
    repos=$(jq  'to_entries
                  | .[]
                  | ["https://" +.value.host + "/" + .value.repo +".zip", .key ]
                  | @sh ' < "$MASTERCONF")
fi
# echo ${repos[@]}
# for r in $repos; do
#     echo $r
#     echo "blank"
# done
# echo "${repos[@]}" | xargs -n2 -I? printf "%s\t%s\n"%?

echo "$repos"
DIR=$(pwd)
cd "$OPALDIR"
set +e
echo "$repos" \
    | xargs -n2 -I% ../safe_clone.sh %
set -e
echo "INFO: finished cloning"
cd "$DIR"
echo "INFO making release tarbal; $TARBALL"
tar zcf $TARBALL $OPALDIR
# | xargs -n1 -I% echo % 
