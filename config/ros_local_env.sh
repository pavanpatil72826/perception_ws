#!/usr/bin/env bash
# Source AFTER humble_dev (which sets ROS_DOMAIN_ID and sources ROS Humble):
#   humble_dev && source ~/Workspace/Workspace/ouster_ws/config/ros_local_env.sh
#
# 1) keeps ROS traffic on this machine
# 2) forces Fast DDS to use shared memory (large segment) for local transport. Without this,
#    ~1.6 MB Ouster point clouds go through UDP loopback and ~half of them get dropped
#    (kernel UDP buffer is 208 KB). With it the full 10 Hz arrives.
# Must be set in EVERY terminal that publishes/subscribes (drivers, polka, rviz, bag play).
_WS="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export ROS_LOCALHOST_ONLY=1
export FASTRTPS_DEFAULT_PROFILES_FILE="$_WS/config/fastdds_shm.xml"
# shellcheck disable=SC1091
source "$_WS/install/setup.bash"
echo "[ros_local_env] domain=${ROS_DOMAIN_ID:-unset} localhost_only=$ROS_LOCALHOST_ONLY profile=$(basename "$FASTRTPS_DEFAULT_PROFILES_FILE")"
unset _WS
