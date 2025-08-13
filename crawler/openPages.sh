#!/bin/bash

INPUT_FILE="./tmp/restaurantes_links.txt"
PROCESSED_FILE="./tmp/processed_urls.txt"
COUNTER_FILE="./tmp/url_counter.log" 


touch "$PROCESSED_FILE"
if [ ! -f "$COUNTER_FILE" ]; then
    echo 0 > "$COUNTER_FILE"
fi

if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: The file '$INPUT_FILE' was not found."
    echo "Copying from source"
    cp ./restaurantes_links.txt ./tmp/restaurantes_links.txt
fi

echo "--- Filtering out already processed URLs from '$PROCESSED_FILE' ---"
tr ',' '\n' < "$INPUT_FILE" | sed '/^$/d' | sort -u > .urls_all.tmp
tr ',' '\n' < "$PROCESSED_FILE" | sed '/^$/d' | sort -u > .urls_processed.tmp

grep -v -x -f .urls_processed.tmp .urls_all.tmp > .urls_unprocessed.tmp

original_count=$(wc -l < .urls_all.tmp)
remaining_count=$(wc -l < .urls_unprocessed.tmp)
removed_count=$((original_count - remaining_count))
echo "$removed_count URLs already processed. Skipping."
echo "$remaining_count URLs remaining to be processed."

paste -s -d, .urls_unprocessed.tmp > "$INPUT_FILE"

rm .urls_all.tmp .urls_processed.tmp .urls_unprocessed.tmp

echo "--- Starting URL processing ---"

while true; do
    file_content=$(cat "$INPUT_FILE")

    if [[ -z "${file_content// }" ]]; then
        echo "File is empty. Processing complete."
        break
    fi

    IFS=','
    read -r -a url_array <<< "$file_content"
    IFS=$' \t\n' 
    current_url=$(echo "${url_array[0]}" | xargs)

    remaining_urls=("${url_array[@]:1}")

    counter=$(cat "$COUNTER_FILE")
    ((counter++))
    echo $counter > "$COUNTER_FILE"

    google-chrome "$current_url"
    echo -n "$current_url," >> "$PROCESSED_FILE"

    (
        IFS=,
        echo -n "${remaining_urls[*]}"
    ) > "$INPUT_FILE"

    # trip advisor fdp
    if (( counter % 3 == 0 )); then
        echo "--- Pausing for 2 seconds ---"
        sleep 1
    fi
    if (( counter % 11 == 0 )); then
        echo "--- Pausing for 2 seconds ---"
        sleep 2
    fi
    if (( counter % 30 == 0 )); then
        echo "--- Pausing for 7 seconds ---"
        sleep 7
    fi
done

rm "$COUNTER_FILE"

echo "------------------------------------"
echo "Process ended - '$INPUT_FILE' is now empty."