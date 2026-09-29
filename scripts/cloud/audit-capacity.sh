#!/usr/bin/env bash
set -euo pipefail

base_path="${PRINTORA_BASE_PATH:-/var/www/print3dmaker.xyz}"
timestamp="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "timestamp_utc=$timestamp"
echo "hostname=$(hostname)"
echo "kernel=$(uname -sr)"
echo "cpu_count=$(getconf _NPROCESSORS_ONLN)"
awk '/MemTotal:/ {print "memory_total_kb=" $2} /MemAvailable:/ {print "memory_available_kb=" $2}' /proc/meminfo
df -Pk "$base_path" | awk 'NR==2 {print "disk_total_kb=" $2; print "disk_available_kb=" $4; print "disk_used_percent=" $5}'
df -Pi "$base_path" | awk 'NR==2 {print "inode_available=" $4; print "inode_used_percent=" $5}'
echo "file_descriptor_limit=$(ulimit -n)"
echo "file_descriptors_allocated=$(awk '{print $1}' /proc/sys/fs/file-nr)"
echo "load_average=$(tr ' ' ',' < /proc/loadavg)"
echo "process_count=$(ps -e --no-headers | wc -l | tr -d ' ')"
if command -v iostat >/dev/null 2>&1; then
  iostat -dx 1 2 | tail -n +1
else
  echo "iostat=unavailable"
fi
ss -s
