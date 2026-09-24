#!/bin/bash 

##########################################################
##                                                      ##
## Shell script for generating a boards manager release ##
## Created by MCUdude                                   ##
## Requires wget, jq and a bash environment             ##
##                                                      ##
##########################################################

# Change these to match your repo
PAOOWNER=felias-fogg # Github owner of PyAvrOCD  
AUTHOR=felias-fogg       # Github user name
REALAUTHOR=felias-fogg   # real author
REPOSITORY=XMiniCore  # Github repo name


# The avrdude the platform depends on has to be one the index actually offers, so
# take the newest entry there rather than a number written down here. Run
# Add_avrdude_release.sh first when a newer avrdude should be used.
AVRDUDE_VERSION=$(jq -r '.packages[].tools[] | select(.name == "avrdude") | .version' \
                  package_${REALAUTHOR}_${REPOSITORY}_index.json | sort -V | tail -1)

if [ -z "$AVRDUDE_VERSION" ]; then
    echo "The index contains no avrdude at all. Run Add_avrdude_release.sh first."
    exit 1
fi
echo "Platform will depend on avrdude ${AVRDUDE_VERSION}"

# Get the version number of most recent PyAvrOCD version
PAOVERSION=$(curl -s https://api.github.com/repos/$PAOOWNER/PyAvrOCD/releases/latest | grep "tag_name" |  awk -F\" '{print $4}')
AVROCDVERSION=${PAOVERSION#"v"}

# A tag may be given as the first argument. Without one we take the latest
# release, as before; with one we take exactly that tag, which is what a
# pre-release needs: the "latest release" of the API never is one.
TAG="$1"

if [ -n "$TAG" ]; then
    DOWNLOAD_URL="https://api.github.com/repos/$AUTHOR/$REPOSITORY/tarball/$TAG"
    DOWNLOADED_FILE="$TAG"
else
    DOWNLOAD_URL=$(curl -s https://api.github.com/repos/$AUTHOR/$REPOSITORY/releases/latest | grep "tarball_url" | awk -F\" '{print $4}')
    DOWNLOADED_FILE=$(echo $DOWNLOAD_URL | awk -F/ '{print $8}')
fi

if [ -z "$DOWNLOADED_FILE" ]; then
    echo "Could not work out which version to package"
    exit 1
fi
echo "Packaging ${DOWNLOADED_FILE}"

# Check whether this exact version is already in the index. The archive name has
# to be matched in full: without the extension, "XMiniCore-1.3.2" also matches
# "XMiniCore-1.3.2-rc5.tar.bz2", and the final release would be refused because
# one of its own release candidates is in the index.
if grep -q "${REPOSITORY}-${DOWNLOADED_FILE#"v"}.tar.bz2" package_${REALAUTHOR}_${REPOSITORY}_index.json; then
    echo "Most recent board version is already in the index file. Nothing to do."
    exit 1
fi

# Check whether already part of the index
if grep -q "avrocd-tools-"${AVROCDVERSION} package_${REALAUTHOR}_${REPOSITORY}_index.json; then
    echo "Current PyAvrOCD version is in index. Continue ..."
else
    echo "Current PyAvrOCD version is not in index. Add it first."
    exit 1
fi

# Download file
wget --no-verbose $DOWNLOAD_URL

# Add .tar.bz2 extension to downloaded file
mv $DOWNLOADED_FILE ${DOWNLOADED_FILE}.tar.bz2

# Extract downloaded file and place it in a folder
printf "\nExtracting folder ${DOWNLOADED_FILE}.tar.bz2 to $REPOSITORY-${DOWNLOADED_FILE#"v"}\n"
mkdir -p "$REPOSITORY-${DOWNLOADED_FILE#"v"}" && tar -xzf ${DOWNLOADED_FILE}.tar.bz2 -C "$REPOSITORY-${DOWNLOADED_FILE#"v"}" --strip-components=1
printf "Done!\n"

### Move files out of the avr folder
##mv $REPOSITORY-${DOWNLOADED_FILE#"v"}/avr/* $REPOSITORY-${DOWNLOADED_FILE#"v"}

# Delete downloaded file and empty avr folder
rm -rf ${DOWNLOADED_FILE}.tar.bz2
##rm -rf $REPOSITORY-${DOWNLOADED_FILE#"v"}/avr

# Make sure there are no macOS related files added to the archive that's soon to be
# generated. dot_clean only exists on macOS; elsewhere there is nothing to clean.
if command -v dot_clean > /dev/null 2>&1; then
    dot_clean .
fi
find . -name "._*" -delete 2>/dev/null

# Compress folder to tar.bz2
printf "\nCompressing folder $REPOSITORY-${DOWNLOADED_FILE#"v"} to $REPOSITORY-${DOWNLOADED_FILE#"v"}.tar.bz2\n"
tar -cjSf $REPOSITORY-${DOWNLOADED_FILE#"v"}.tar.bz2 $REPOSITORY-${DOWNLOADED_FILE#"v"}
printf "Done!\n"

# Get file size on bytes
FILE_SIZE=$(wc -c "$REPOSITORY-${DOWNLOADED_FILE#"v"}.tar.bz2" | awk '{print $1}')

# Get SHA256 hash
# shasum is a macOS thing, sha256sum a Linux one
if command -v shasum > /dev/null 2>&1; then
    SHA256="SHA-256:$(shasum -a 256 "$REPOSITORY-${DOWNLOADED_FILE#"v"}.tar.bz2" | awk '{print $1}')"
else
    SHA256="SHA-256:$(sha256sum "$REPOSITORY-${DOWNLOADED_FILE#"v"}.tar.bz2" | awk '{print $1}')"
fi

# Create Github download URL
URL="https://${AUTHOR}.github.io/${REPOSITORY}/$REPOSITORY-${DOWNLOADED_FILE#"v"}.tar.bz2"

cp "package_${REALAUTHOR}_${REPOSITORY}_index.json" "package_${REALAUTHOR}_${REPOSITORY}_index.json.tmp"

# Add new boards release entry
jq -r                                    \
--arg avrocdversion $AVROCDVERSION     \
--arg repository  $REPOSITORY            \
--arg version     ${DOWNLOADED_FILE#"v"} \
--arg url         $URL                   \
--arg checksum    $SHA256                \
--arg file_size   $FILE_SIZE             \
--arg avrdude_ver $AVRDUDE_VERSION       \
--arg file_name   $REPOSITORY-${DOWNLOADED_FILE#"v"}.tar.bz2  \
'.packages[].platforms[.packages[].platforms | length] |= . +
{
  "name": "XMiniCore",
  "architecture": "avr",
  "version": $version,
  "category": "Contributed",
  "url": $url,
  "archiveFileName": $file_name,
  "checksum": $checksum,
  "size": $file_size,
  "boards": [
            {
              "name": "Atmel atmega328p Xplained mini"
            },
            {
              "name": "Atmel atmega328pb Xplained mini"
            },
            {
              "name": "Atmel atmega168pb Xplained mini"
            }
  ],
    "toolsDependencies": [
    {
      "packager": "arduino",
      "name": "avr-gcc",
      "version": "7.3.0-atmel3.6.1-arduino7"
    },
    {
      "packager": "XMiniCore",
      "name": "avrdude",
      "version": $avrdude_ver
    },
    {
      "packager": "arduino",
      "name": "arduinoOTA",
      "version": "1.3.0"
    },
    {
      "packager": "XMiniCore",
      "name": "avrocd-tools",
      "version": $avrocdversion
    }   
  ]
}' "package_${REALAUTHOR}_${REPOSITORY}_index.json.tmp" > "package_${REALAUTHOR}_${REPOSITORY}_index.json"

# Remove files that are no longer needed
rm -rf "$REPOSITORY-${DOWNLOADED_FILE#"v"}" "package_${REALAUTHOR}_${REPOSITORY}_index.json.tmp"
