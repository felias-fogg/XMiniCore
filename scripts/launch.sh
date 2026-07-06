#!/bin/bash
# Parameters
# $1 = build.source.path
# $2 = build.mcu
# $3 = debug.executable
# $4 = debug.toolchain.path
# $5 = runtime.tools.avr-gcc.path
# $6 = build.f_cpu
# $7 = simavr
# $8 = prelaunch1
# $9 = prelaunch2

# construct -s argument
if [ -z "$7" ]; then
    start="nop"
else
    start=$7
fi

# check for .vscode
if [ ! -d "$1/.vscode" ]; then
    echo "No .vscode folder"
    exit
fi
# check if already there
if grep -q "\"name\": \"Arduino Debug $2\"" "$1/.vscode/launch.json" 2>/dev/null; then
    if grep -q \"$start\" 2>/dev/null; then
       echo "launch.json already exists"
       exit
fi
# construct prelaunch commands string
if [[ -n "$8" ]]; then
    prelaunch=$(cat << EOF
,
            "preLaunchCommands": [
                "$7",
                "$8"
            ]
EOF
)
elif  [[ -n "$7" ]]; then
    prelaunch=$(cat << EOF
,
            "preLaunchCommands": [
                "$7"
            ]
EOF
)
else
    prelaunch=""
fi

cat > "$1/.vscode/launch.json" <<EOF 
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Arduino Debug $2",
            "cwd": "\${workspaceRoot}",
            "request": "launch",
            "type": "cortex-debug",
            "executable": "$3",
            "svdFile": "$4/pyavrocd-util/svd/$2.svd",
            "gdbPath": "$4/avr-gdb",
            "objdumpPath": "$5/bin/avr-objdump",
            "overrideGDBServerStartedRegex": "Listening on port \\\\d+ for gdb connection",
            "runToEntryPoint": "main",
            "serverArgs": [
                "-s",
                "$start",
                "--device",
                "$2",
                "--manage",
                "all",
                "--F_CPU",
                "$6",
                "--prog-clock",
                "2000"
            ],
            "serverpath": "$4/pyavrocd",
            "servertype": "openocd",
            "armToolchainPath": "$4",
            "configFiles": [
                "nix"
            ]$prelaunch
        }
    ]
}
EOF