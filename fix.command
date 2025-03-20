#!/bin/bash

# Allow Finder to handle spaces in paths
export IFS=$'\n'

# Set the directory to scan
DIR="/Volumes/z2/"

# Rename files by removing commas
find "$DIR" -type f -name '*,*' | while IFS= read -r file; do
    newname="${file//,/}"
    if [ "$file" != "$newname" ]; then
        mv "$file" "$newname"
        echo "Renamed: $file → $newname"
    fi
done

# Rename files by removing hash symbols (#)
find "$DIR" -type f -name '*#*' | while IFS= read -r file; do
    newname="${file//\#/}"
    if [ "$file" != "$newname" ]; then
        mv "$file" "$newname"
        echo "Renamed: $file → $newname"
    fi
done

echo "Done!"
read -p "Press Enter to exit..."