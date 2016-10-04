#!/usr/bin/env bash
set -e
MASTERCONF=./master_conf.json
OPALDIR=opals-sources
TARBALL=opals.tar.gz
CLONE="clone"
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

DIR=$(pwd)
cd "$OPALDIR"
echo "$repos" \
    | xargs -n2 -I% ../safe_clone.sh %
cd "$DIR"
echo "INFO making release tarbal; $TARBALL"
tar zcf $TARBALL $OPALDIR
# | xargs -n1 -I% echo % 
