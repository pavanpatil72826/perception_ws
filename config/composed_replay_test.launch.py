# TEST launch: Ouster cloud processors (front + rear) and POLKA in ONE container with
# intra-process communication, fed from the raw lidar packets of a recorded bag.
# The point clouds never leave the process, so no DDS transport / UDP fragmentation.
#
# Terminal A:  ros2 launch ~/Workspace/Workspace/ouster_ws/config/composed_replay_test.launch.py
# Terminal B:  ros2 bag play rosbag2_2026_11_20-14_11_29 --clock --loop --topics \
#                /drwig_Front_licam/lidar_packets /drwig_Rear_licam/lidar_packets /tf_static
import os

from launch import LaunchDescription
from launch_ros.actions import ComposableNodeContainer, Node
from launch_ros.descriptions import ComposableNode

WS = os.path.expanduser('~/Workspace/Workspace/ouster_ws')
POLKA_PARAMS = os.path.join(WS, 'config', 'polka_ouster_dual.yaml')
LIDARS = ['drwig_Front_licam', 'drwig_Rear_licam']
INTRA = [{'use_intra_process_comms': True}]


def generate_launch_description():
    actions = []
    composable = []

    for ns in LIDARS:
        # publishes the sensor metadata (read from the json the driver wrote) for os_cloud
        actions.append(Node(
            package='ouster_ros', executable='os_replay', name='os_replay', namespace=ns,
            output='screen',
            parameters=[{'metadata': os.path.join(WS, f'{ns}_metadata.json'),
                         'use_sim_time': True}]))

        composable.append(ComposableNode(
            package='ouster_ros', plugin='ouster_ros::OusterCloud',
            name='os_cloud', namespace=ns,
            parameters=[{
                'sensor_frame': ns, 'lidar_frame': f'{ns}_lidar', 'imu_frame': f'{ns}_imu',
                'point_cloud_frame': '',
                'pub_static_tf': False,                 # TF comes from the bag's /tf_static
                'timestamp_mode': 'TIME_FROM_ROS_TIME',  # stamp with (sim) ROS time
                'proc_mask': 'PCL',
                'use_sim_time': True,
            }],
            extra_arguments=INTRA))

    composable.append(ComposableNode(
        package='polka', plugin='polka::PolkaNode', name='polka',
        parameters=[POLKA_PARAMS, {'use_sim_time': True}],
        extra_arguments=INTRA))

    actions.append(ComposableNodeContainer(
        name='lidar_container', namespace='', package='rclcpp_components',
        executable='component_container_mt', composable_node_descriptions=composable,
        output='screen'))
    return LaunchDescription(actions)
