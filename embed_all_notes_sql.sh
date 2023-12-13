#!/bin/bash

# Specify the directory containing the .txt files
directory="./notes"

#conda activate coding

# Loop through all .txt files in the directory
for file in "$directory"/*.txt; do
    # Check if the file exists
    if [ -e "$file" ]; then
        # Extract the file name (without extension) from the full path
        filename=$(basename "$file" .txt)
        
        # Run the embed.py command for the current file
        python3 embed_sql.py --path "$file" --tokenlim 350 
        
        # Optionally, you can print a message indicating which file is being processed
        echo "Processed: $filename"
    fi
done

