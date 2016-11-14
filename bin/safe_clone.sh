#!/usr/bin/env bash
safe_clone () {
    REPO="$1"
    DEST="$2"
    echo git clone "$REPO" "$DEST"
    if [ -r "$DEST" ]; then
        echo "WARN: Directory $DEST already exists"
        return 1
    fi
    if ! git clone -b dev "$REPO" "$DEST"; then
        echo "WARN: failed to download dev branch of $DEST. trying HEAD"
        git clone "$REPO" "$DEST"
    fi
    return $?
}

safe_clone $1 $2
exit $?
