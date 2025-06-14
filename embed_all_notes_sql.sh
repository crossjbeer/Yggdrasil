#!/bin/bash

# Specify the directory containing the .txt files
directory="./notes"

#conda activate coding

# >>> conda initialize >>>
# !! Contents within this block are managed by 'conda init' !!
__conda_setup="$('/Users/crossland/miniconda3/bin/conda' 'shell.bash' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "/Users/crossland/miniconda3/etc/profile.d/conda.sh" ]; then
        . "/Users/crossland/miniconda3/etc/profile.d/conda.sh"
    else
        export PATH="/Users/crossland/miniconda3/bin:$PATH"
    fi
fi
unset __conda_setup
# <<< conda initialize <<<
conda activate yggy

# Loop through all .txt files in the directory
for file in "$directory"/*.txt; do
    # Check if the file exists
    if [ -e "$file" ]; then
        # Extract the file name (without extension) from the full path
        filename=$(basename "$file" .txt)
        
        # Run the embed.py command for the current file
        python3 pg_embed.py --path "$file" --tokenlim 1200 --database yggdrasil --namespace notes --lag 6 --embedding_model text-embedding-3-small
        
        # Optionally, you can print a message indicating which file is being processed
        echo "Processed: $filename"
    fi
done

