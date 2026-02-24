#!/usr/bin/env bash

# Robust Star Checker v2
# Usage: ./check_star.sh <issue_number>

ISSUE_NUM=$1
if [ -z "$ISSUE_NUM" ]; then exit 2; fi

# 1. Get Repo and Author info
REPO_FULL=$(gh repo view --json owner,name -q ".owner.login + \"/\" + .name")
USER_LOGIN=$(gh issue view "$ISSUE_NUM" --json author -q ".author.login")

# 2. Use GraphQL for high precision (Detects stars even when REST 404s)
IS_STARRED=$(gh api graphql -f query='
query($owner:String!, $repo:String!, $user:String!) {
  repository(owner:$owner, name:$repo) {
    stargazers(query:$user, first:1) {
      nodes {
        login
      }
    }
  }
}' -f owner="${REPO_FULL%/*}" -f repo="${REPO_FULL#*/}" -f user="$USER_LOGIN" -q ".data.repository.stargazers.nodes[0].login")

if [ "$IS_STARRED" == "$USER_LOGIN" ]; then
    echo "Confirmed: @$USER_LOGIN HAS starred $REPO_FULL. ⭐"
    exit 0
else
    echo "Confirmed: @$USER_LOGIN has NOT starred $REPO_FULL."
    exit 1
fi
