#!/bin/bash

# Toggle check
[ -f ".../.disabled" ] && exit

# Detect + notify
if patterns_found; then
  jq '{"systemMessage": "✓"}'
fi

# /reflect on | /reflect off to toggle