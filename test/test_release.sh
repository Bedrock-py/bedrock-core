#/usr/bin/env bash
pushd bin/
./release.sh ../master_conf.json opals-sources opals.tar.gz clone
if [! -r opals.tar.gz ];
then
    echo "failed to make tarball"
    exit 1
fi
if [! -r opals-sources ];
then
    echo "failed to get source code tree"
    exit 2
fi
popd
