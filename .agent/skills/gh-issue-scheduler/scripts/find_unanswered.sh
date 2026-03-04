#!/usr/bin/env bash

# Fetch all open issues and filter for those without responses from the owner/collaborators.
# Uses 'gh' CLI.

REPO_FULL=$(gh repo view --json owner,name -q ".owner.login + "/" + .name")
OWNER=${REPO_FULL%/*}

# 1. Get all open issues
OPEN_ISSUES=$(gh issue list --state open --json number,title,author,createdAt --limit 100)

echo "Analysis for repository: $REPO_FULL"
echo "------------------------------------"

# Process each issue
echo "$OPEN_ISSUES" | jq -c '.[]' | while read -r issue; do
    NUMBER=$(echo "$issue" | jq -r '.number')
    TITLE=$(echo "$issue" | jq -r '.title')
    AUTHOR=$(echo "$issue" | jq -r '.author.login')
    
    # Check comments for owner responses
    # We look for comments where the author is the repo owner
    COMMENTS=$(gh issue view "$NUMBER" --json comments -q ".comments[].author.login" 2>/dev/null)
    
    HAS_OWNER_REPLY=false
    for COMMENT_AUTHOR in $COMMENTS; do
        if [ "$COMMENT_AUTHOR" == "$OWNER" ]; then
            HAS_OWNER_REPLY=true
            break
        fi
    done
    
    if [ "$HAS_OWNER_REPLY" == "false" ]; then
        echo "ISSUE_START"
        echo "ID: $NUMBER"
        echo "Title: $TITLE"
        echo "Author: $AUTHOR"
        echo "Description:"
        gh issue view "$NUMBER" --json body -q ".body"
        echo "ISSUE_END"
    fi
done
