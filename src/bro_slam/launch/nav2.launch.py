from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():

    pkg= get_package_share_directory("bro_slam")
    use_sim_time = LaunchConfiguration('use_sim_time')
    map_yaml_file = os.path.join(pkg, "maps", "DSP_lab.yaml")
    params_file =  os.path.join(pkg, "config", "tb_navigation.yaml")
    amcl_file= os.path.join(pkg, "config", "tb_localization.yaml")

    return LaunchDescription([

        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false'
        ),

        # DeclareLaunchArgument(
        #     'map',
        #     default_value='/home/jarvis/maps/my_map.yaml'  # change path
        # ),

        # DeclareLaunchArgument(
        #     'params_file',
        #     default_value='/home/jarvis/nav2_params.yaml'  # your config file
        # ),

        # Map Server
        Node(
            package='nav2_map_server',
            executable='map_server',
            name='map_server',
            output='screen',
            parameters=[{
                'yaml_filename': map_yaml_file
            }]
        ),

        # AMCL
        Node(
            package='nav2_amcl',
            executable='amcl',
            name='amcl',
            output='screen',
            parameters=[amcl_file]
        ),

        # Planner
        Node(
            package='nav2_planner',
            executable='planner_server',
            name='planner_server',
            output='screen',
            parameters=[params_file]
        ),

        # Controller
        Node(
            package='nav2_controller',
            executable='controller_server',
            name='controller_server',
            output='screen',
            parameters=[params_file]
        ),

        # Behavior Tree Navigator
        Node(
            package='nav2_bt_navigator',
            executable='bt_navigator',
            name='bt_navigator',
            output='screen',
            parameters=[params_file]
        ),

        # Costmaps
        Node(
            package='nav2_costmap_2d',
            executable='costmap_2d',
            name='local_costmap',
            output='screen',
            parameters=[params_file]
        ),

        Node(
            package='nav2_costmap_2d',
            executable='costmap_2d',
            name='global_costmap',
            output='screen',
            parameters=[params_file]
        ),

        # Lifecycle Manager
        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_navigation',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'autostart': True,
                'node_names': [
                    'map_server',
                    'amcl',
                    'planner_server',
                    'controller_server',
                    'bt_navigator',
                    'local_costmap',
                    'global_costmap'
                    'behavior_server',
                    'smoother_server',
                    'waypoint_follower',
                    'velocity_smoother',
                    'collision_monitor',
                ]
            }]
        ),
        Node(
            package='nav2_behaviors',
            executable='behavior_server',
            name='behavior_server',
            output='screen',
            parameters=[params_file]
        ),

        Node(
            package='nav2_smoother',
            executable='smoother_server',
            name='smoother_server',
            output='screen',
            parameters=[params_file]
        ),

        Node(
            package='nav2_waypoint_follower',
            executable='waypoint_follower',
            name='waypoint_follower',
            output='screen',
            parameters=[params_file]
        ),

        Node(
            package='nav2_velocity_smoother',
            executable='velocity_smoother',
            name='velocity_smoother',
            output='screen',
            parameters=[params_file]
        ),

        Node(
            package='nav2_collision_monitor',
            executable='collision_monitor',
            name='collision_monitor',
            output='screen',
            parameters=[params_file]
        ),
    ])