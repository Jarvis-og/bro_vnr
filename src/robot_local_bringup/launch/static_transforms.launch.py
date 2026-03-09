from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    imu_tf= Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['0.10', '0.13', '0', '0', '0', '0', 'base_link', 'imu_link']
    )

    lidar_tf= Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments= ['0', '0', '0.14', '0', '0', '0', 'base_link', 'laser']
    )

    return LaunchDescription([imu_tf, lidar_tf])