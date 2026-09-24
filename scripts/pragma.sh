#!/bin/bash
# Parameters
# $1 = compiler command
# $2 = sketch path
# $3 = build path
# $4 = build project name
# $5.. = flag names ('cpp_flags', 'release_flags', 'debug_flags')
#
# All flag names are handled in one go: they are looked for in the same
# preprocessed source, and preprocessing it is the expensive part.

COMPILER="$1"
SKETCH_PATH="$2"
BUILD_PATH="$3"
PROJECT_NAME="$4"
shift 4

if [ "$#" -eq 0 ]; then
    echo "usage: pragma.sh <compiler> <sketch path> <build path> <project> <flag> ..."
    exit 1
fi

PREPROCESSED="$BUILD_PATH/pragma_preproc.tmp"
"$COMPILER" -fpreprocessed -dD -E -x c++ "$SKETCH_PATH/$PROJECT_NAME" >"$PREPROCESSED"

changed=0

for flag in "$@"; do
    out="$BUILD_PATH/options.$flag"
    touch "$out"                       # so that the first run has something to compare
    cp "$out" "$out.bak"
    grep -E "^\s*#\s*pragma\s+arduino\s+$flag" "$PREPROCESSED" \
        | sed -E 's/# *pragma +arduino +(debug|release|cpp)_flags//g' \
        | tr '\n' ' ' >"$out"
    if [[ $(diff -q "$out" "$out.bak") ]]; then
        changed=1
    fi
    rm "$out.bak"
done

# When any of them changed, the cached object files were built with other flags
# and have to go: all cached *.o and *.a files, and the cached cores as well. Go
# up one directory level; if there are only two directories called 'sketches'
# and 'cores', and 'cores' contains only directories with just one file
# 'core.a', then delete the 'cores' folder.
if [[ $changed -eq 1 ]]; then
    echo "Options changed: Delete cached object files"
    rm -rf "$BUILD_PATH/core/"*.a
    rm -rf "$BUILD_PATH/core/"*.o
    rm -rf "$BUILD_PATH/sketch/"*.a

    if [[ -d $BUILD_PATH/../../cores ]] && [[ -d $BUILD_PATH/../../sketches ]]; then
        filenums=$(find "$BUILD_PATH"/../../ -maxdepth 1 -print | wc -l)
        if [[ $filenums -eq 3 ]]; then
            corefolders=$(find "$BUILD_PATH"/../../cores -type d -print | wc -l)
            immediate=$(find "$BUILD_PATH"/../../cores -maxdepth 1 -print | wc -l)
            corefiles=$(find "$BUILD_PATH"/../../cores -type f -name "core.a" -print -or -name ".last-used" -print | wc -l)
            if [[ $((corefiles/2)) -eq $((corefolders-1)) ]] && [[ $corefolders -eq $immediate ]]; then
                echo "Delete cached cores"
                rm -rf "$BUILD_PATH"/../../cores
            fi
        fi
    fi
fi
