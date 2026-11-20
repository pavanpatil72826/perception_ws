# perception_ws

ROS 2 Humble workspace for a dual Ouster OS-1-32 (Front + Rear) lidar setup: driver launch,
extrinsic calibration (Multi_LiCa), and point cloud fusion (POLKA).

Source repos are not stored here (see `repos.yaml`); this repo holds configs, patches and notes.

## Layout
- `repos.yaml` - source repos + pinned revisions
- `patches/` - local changes to upstream repos (Multi_LiCa NaN/QoS fixes + `coarse_method`, TEASER++ GCC fix)
- `config/polka_ouster_dual.yaml` - POLKA: merge both clouds into `imu_link`, output `/polka/merged_cloud`
- `config/polka_view.rviz` - RViz view of the merged cloud (use with `use_sim_time:=true` for bag replay)
- `config/fastdds_shm.xml`, `config/ros_local_env.sh` - Fast DDS shared-memory transport (see below)
- `config/composed_replay_test.launch.py` - experiment: drivers+POLKA in one container (does not work yet)

## Environment (every terminal)
    humble_dev                      # ROS_DOMAIN_ID=2 + source humble (bashrc function)
    source config/ros_local_env.sh  # localhost-only + shared-memory DDS profile + source install/

**Why the profile:** each Ouster cloud is ~1.6 MB. Over the default Fast DDS UDP loopback the 208 KB
kernel socket buffer overflows and 40-80% of the clouds are lost (2-6 Hz received instead of 10 Hz).
With the shared-memory profile the full 10 Hz arrives. Needs to be set in *every* process.

## Setup
    vcs import src < repos.yaml
    git -C src/ouster-ros submodule update --init --recursive
    git -C src/Multi_LiCa submodule update --init
    git -C src/Multi_LiCa am ../../patches/multi_lica/*.patch
    git -C src/Multi_LiCa/TEASER-plusplus apply ../../../patches/teaser-plusplus-graph-cc.patch
    # TEASER++ python bindings (build + pip install), ros2_numpy via pip, then:
    colcon build --symlink-install --packages-select ouster_sensor_msgs ouster_ros multi_lidar_calibrator
    colcon build --symlink-install --packages-select polka --cmake-args -DWITH_CUDA=OFF

## Run live
    ros2 launch ouster_ros dual_lidar.launch.py
    ros2 run polka polka_node --ros-args --params-file config/polka_ouster_dual.yaml

## Test on a bag (no sensors)
Ouster stamps are the sensors' internal clocks, so restamp first (POLKA drops sources by header stamp):
bags recorded with `TIME_FROM_ROS_TIME` (set in `dual_lidar.launch.py`) don't need this.

    ros2 run polka polka_node --ros-args --params-file config/polka_ouster_dual.yaml -p use_sim_time:=true
    ros2 bag play <bag> --clock --loop
    rviz2 -d config/polka_view.rviz --ros-args -p use_sim_time:=true

## Calibration notes (Multi_LiCa)
Table rows are the pose of the *lidar* frame in `imu_link` = static-TF sensor yaw + 180 deg
(sensor->lidar is Rz(180) in the metadata). Result is the correction on top of that guess.
