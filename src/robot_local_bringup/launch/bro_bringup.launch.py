#!/usr/bin/env python3

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    # Define parameters
    channel_type = DeclareLaunchArgument(
        'channel_type',
        default_value='serial',
        description='Specifying channel type of lidar'
    )
    
    serial_port_stm = DeclareLaunchArgument(
        'serial_port',
        default_value='/dev/ttyACM0',
        description='Specifying usb port to connected lidar'
    )

    serial_port_lidar = DeclareLaunchArgument(
        'serial_port',
        default_value='/dev/ttyUSB0',
        description='Specifying usb port to connected lidar'
    )
    
    serial_baudrate_stm = DeclareLaunchArgument(
        'serial_baudrate',
        default_value='115200',
        description='Specifying usb port baudrate to connected lidar'
    )

    serial_baudrate_lidar = DeclareLaunchArgument(
        'serial_baudrate',
        default_value='460800',
        description='Specifying usb port baudrate to connected lidar'
    )
    
    frame_id = DeclareLaunchArgument(
        'frame_id',
        default_value='laser',
        description='Specifying frame_id of lidar'
    )
    
    inverted = DeclareLaunchArgument(
        'inverted',
        default_value='false',
        description='Specifying whether or not to invert scan data'
    )
    
    angle_compensate = DeclareLaunchArgument(
        'angle_compensate',
        default_value='true',
        description='Specifying whether or not to enable angle_compensate of scan data'
    )
    
    scan_mode = DeclareLaunchArgument(
        'scan_mode',
        default_value='Standard',
        description='Specifying scan mode of lidar'
    )
    
    # Define nodes
    imu_node = Node(
        package='imu_mpu',
        executable='imu_node',
        name='imu_node',
        output='screen'
    )
    
    odom_node = Node(
        package='motor_control',
        executable='odom_node',
        name='odom_node',
        output='screen'
    )
    
    ekf_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_node',
        parameters=[
            FindPackageShare('robot_local_bringup') + '/config/ekf.yaml'
        ],
        output='screen'
    )

    motor_driver = Node(
        package='motor_control',
        executable='motor_driver',
        name='motor_driver',
        parameters=[
            {'port': LaunchConfiguration('serial_port_stm'),
             'baud': LaunchConfiguration('serial_baudrate_stm')}
        ],
        output='screen'
    )
    
    sllidar_node = Node(
        package='sllidar_ros2',
        executable='sllidar_node',
        name='sllidar_node',
        parameters=[
            {'channel_type': LaunchConfiguration('channel_type'),
             'serial_port': LaunchConfiguration('serial_port_lidar'), 
             'serial_baudrate': LaunchConfiguration('serial_baudrate_lidar'), 
             'frame_id': LaunchConfiguration('frame_id'),
             'inverted': LaunchConfiguration('inverted'), 
             'angle_compensate': LaunchConfiguration('angle_compensate'), 
             'scan_mode': LaunchConfiguration('scan_mode')}
        ],
        output='screen'
    )
    
    # Define static transforms
    imu_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['0.10', '0.13', '0', '0', '0', '0', 'base_link', 'imu_link'],
        output='screen'
    )
    
    lidar_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['0', '0', '0.14', '0', '0', '0', 'base_link', 'laser'],
        output='screen'
    )
    
    # Define the main launch description
    return LaunchDescription([
        # Declare parameters
        channel_type,
        serial_port_lidar,
        serial_port_stm,
        serial_baudrate_lidar,
        serial_baudrate_stm,
        frame_id,
        inverted,
        angle_compensate,
        scan_mode,
        
        # Declare nodes
        imu_node,
        odom_node,
        ekf_node,
        motor_driver,
        sllidar_node,
        
        # Declare static transforms
        imu_tf,
        lidar_tf
    ])