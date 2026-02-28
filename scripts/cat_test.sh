#!/usr/bin/env bash
set -euo pipefail

DEV="${1:-/dev/ttyACM0}"

if [[ ! -e "$DEV" ]]; then
  echo "Device not found: $DEV" >&2
  echo "Usage: $0 /dev/ttyACM0" >&2
  exit 1
fi

# Configure serial port for raw 115200 8N1.
stty -F "$DEV" 115200 cs8 -cstopb -parenb -ixon -ixoff -icanon -echo min 0 time 5

exec 3<> "$DEV"

exchange() {
  local cmd="$1"
  local resp=""
  local deadline=$((SECONDS + 2))

  printf "%s" "$cmd" >&3

  # Read until ';' or timeout.
  while (( SECONDS < deadline )); do
    local ch
    if IFS= read -r -n 1 -t 0.2 -u 3 ch; then
      ch=${ch//$'\r'/}
      ch=${ch//$'\0'/}
      if [[ -n "$ch" ]]; then
        resp+="$ch"
        if [[ "$ch" == ";" ]]; then
          break
        fi
      fi
    fi
  done

  if [[ -n "$resp" ]]; then
    printf "> %s\n< %s\n\n" "$cmd" "$resp"
  else
    printf "> %s\n< (no response)\n\n" "$cmd"
  fi
}

exchange "FA;"
exchange "FB;"
exchange "MD;"
exchange "IF;"
exchange "TX;"
exchange "RX;"
exchange "AG;"
exchange "RG;"
exchange "SM;"
exchange "GT;"
exchange "KS;"
