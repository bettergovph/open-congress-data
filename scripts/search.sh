#!/bin/bash

# Search functions
DIRECTORY="data/person"

# Function to search exact ID
search_exact_id(){
    local search_id="$1"
    echo "Searching for the exact ID: '$search_id'"

    # Search for files that matches with the ID with any file extensions
    find "$DIRECTORY" -type f -name "${search_id}.*" 2>/dev/null

    # Search for the filename without extension
    find "$DIRECTORY" -type f -name "$search_id" 2>/dev/null

}

search_partial_id(){
    local search_id ="$1"
    echo "Searching for the partial ID match: '$search_id'"

    # Search for files containing the ID
    find "$DIRECTORY" -type f -name "${search_id}*" 2>dev>null 
} 

# Function to get file details
get_file_details() {
    local filepath="$1"
    if [ -f "$filepath" ]; then
        echo "File Details:"
        echo "Path: $filepath"
        echo "  Size: $(stat -f%z "$filepath" 2>/dev/null || stat -c%s "$filepath" 2>/dev/null) bytes"
        echo "  Modified: $(stat -f%Sm "$filepath" 2>/dev/null || stat -c%y "$filepath" 2>/dev/null)"
        echo "  First line:"
        head -n 1 "$filepath" 2>/dev/null | sed 's/^/    /'
    fi
}

main() {
    if [ ! -d "$DIRECTORY" ]; then
        echo "Error: Directory '$DIRECTORY' does not exist!"
        exit 1
    fi
    
    case "${1:-}" in
        "exact")
            if [ -z "$2" ]; then
                echo "Usage: $0 exact <ID>"
                exit 1
            fi
            search_exact_id "$2"
            ;;
        "partial")
            if [ -z "$2" ]; then
                echo "Usage: $0 partial <ID>"
                exit 1
            fi
            search_partial_id "$2"
            ;;
        "list")
            list_all_ids
            ;;
        "ext")
            if [ -z "$2" ]; then
                echo "Usage: $0 ext <extension>"
                exit 1
            fi
            list_ids_by_extension "$2"
            ;;
        "details")
            if [ -z "$2" ]; then
                echo "Usage: $0 details <filepath>"
                exit 1
            fi
            get_file_details "$2"
            ;;
        *)
            echo "ID Search Tool"
            echo "============="
            echo "Usage:"
            echo "  $0 exact <ID>        - Search for exact ID match"
            echo "  $0 partial <ID>      - Search for partial ID match"
            echo "  $0 list              - List all IDs in directory"
            echo "  $0 ext <extension>   - List IDs with specific extension"
            echo "  $0 details <file>    - Get details of a specific file"
            echo ""
            echo "Examples:"
            echo "  $0 exact B001230"
            echo "  $0 partial B001"
            echo "  $0 ext csv"
            echo "  $0 list"
            ;;
    esac
}

main "$@"
