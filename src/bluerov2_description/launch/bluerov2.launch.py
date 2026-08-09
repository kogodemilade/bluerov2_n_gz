#!/usr/bin/env python3

"""
Launch multiple BlueROV2 instances using ArduSub SITL and Gazebo,
with camera/odometry bridges, TF, and per-robot ORB-SLAM3.
"""

import os
from pathlib import Path

from ament_index_python.packages import (
    get_package_share_directory,
    get_package_prefix,
)

from jinja2 import Environment, FileSystemLoader

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    AppendEnvironmentVariable,
    OpaqueFunction,
    SetEnvironmentVariable,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.actions import SetParameter
from launch.conditions import IfCondition, UnlessCondition
from launch_ros.parameter_descriptions import ParameterValue
from launch.actions import ExecuteProcess
import shutil

# ---------------------------------------------------------------------------
# Generate N robot models
# ---------------------------------------------------------------------------

def spawn_n_robots(context, *args, **kwargs):

    n = int(LaunchConfiguration('number').perform(context))
    robots_list = []

    share_dir = Path(
        get_package_share_directory('bluerov2_description')
    )

    models_source_dir = share_dir / 'models' / 'bluerov2'

    env = Environment(
        loader=FileSystemLoader(str(models_source_dir))
    )

    model_template = env.get_template('model.sdf.jinja')
    config_template = env.get_template('model.config.jinja')

    base_dir = Path('~/bluerov2_n_gz').expanduser()
    models_dir = base_dir / 'generated_models'

    # clean previous run
    if models_dir.exists():
        shutil.rmtree(models_dir)


    models_dir.mkdir(parents=True, exist_ok=True)

    for i in range(n):

        robot = {
            'name': f'robot_{i}',
            'namespace': f'robot_{i}',
            'fdm_port': 9002 + i * 10,
            'mavlink_port': 14550 + i,
            'x': i * 5,
            'y': 0,
            'z': -2,
        }
        robots_list.append(robot)

        rendered = model_template.render(robot=robot)

        robot_dir = models_dir / robot['name']
        robot_dir.mkdir(parents=True, exist_ok=True)

        with open(robot_dir / 'model.sdf', 'w') as f:
            f.write(rendered)

        config = config_template.render(robot=robot)

        with open(robot_dir / 'model.config', 'w') as f:
            f.write(config)

    # rviz_dir = Path(get_package_share_directory("orca_bringup")) / 'rviz'
    # rviz_env = Environment(loader=FileSystemLoader(str(rviz_dir)))
    # rviz_template = rviz_env.get_template('sim.rviz.jinja')
    # rviz_rendered = rviz_template.render(robots_list=robots_list)

    # with open(rviz_dir / 'gen_sim.rviz', 'w') as f:
    #     f.write(rviz_rendered)

    return [
        AppendEnvironmentVariable(
            name='GZ_SIM_RESOURCE_PATH',
            value=str(models_dir),
        ),
        # Node(
        #     package='rviz2',
        #     executable='rviz2',
        #     output='screen',
        #     parameters=[
        #         {
        #             'use_sim_time': True,
        #         }
        #     ],
        #     arguments=['-d', os.path.join(get_package_share_directory('orca_bringup'), 'rviz', 'gen_sim.rviz')],
        # )
    ]


# ---------------------------------------------------------------------------
# Generate world and launch Gazebo
# ---------------------------------------------------------------------------

def generate_world(context, *args, **kwargs):

    n = int(LaunchConfiguration('number').perform(context))

    share_dir = Path(
        get_package_share_directory('bluerov2_description')
    )

    worlds_dir = share_dir / 'worlds'

    env = Environment(
        loader=FileSystemLoader(str(worlds_dir))
    )

    template = env.get_template(
        'bluerov2_underwater.world.jinja'
    )

    robot_names = []

    for i in range(n):
        robot_names.append({
            'name': f'robot_{i}',
            'x': i * 5,
            'y': 0,
            'z': -2,
        })

    rendered = template.render(
        robot_names=robot_names
    )

    base_dir = Path('~/bluerov2_n_gz').expanduser()
    world_file = base_dir / 'world.sdf'

    if world_file.exists():
        world_file.unlink()

    base_dir.mkdir(parents=True, exist_ok=True)

    with open(world_file, 'w') as f:
        f.write(rendered)

    return [
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(
                    get_package_share_directory('ros_gz_sim'),
                    'launch',
                    'gz_sim.launch.py',
                )
            ),
            launch_arguments={
                'gz_args': [
                    '-r -s -v4 ',
                    str(world_file),
                ],
                'on_exit_shutdown': 'true',
            }.items(),
        )
    ]


# ---------------------------------------------------------------------------
# NEW: ported from the single-robot orca5 launch file
# (ArduSub itself is intentionally NOT launched here -- start it manually
# per robot in separate terminals, matching each instance's -I<n> to the
# fdm_port values in spawn_n_robots() (9002 + i*10) and picking a distinct
# --out MAVLink port per instance, e.g. 14550 + i.)
# ---------------------------------------------------------------------------

def launch_perception_and_slam(context, *args, **kwargs):

    n = int(LaunchConfiguration('number').perform(context))

    camera_info_url = LaunchConfiguration(
        'camera_info_url'
    ).perform(context)

    orb_slam = LaunchConfiguration('orb').perform(context)
    slam_bridge = LaunchConfiguration('bridge').perform(context)
    use_vpe = LaunchConfiguration('use_vpe').perform(context)
    use_sim_time = LaunchConfiguration('use_sim_time').perform(context)

    orca_bringup_dir = get_package_share_directory('orca_bringup')
    sub_common_parm_file = os.path.join(orca_bringup_dir, 'config', 'sub_common.parm')
    sub_vpd_parm_file = os.path.join(orca_bringup_dir, 'config', 'sub_vpd.parm')
    sub_vpe_parm_file = os.path.join(orca_bringup_dir, 'config', 'sub_vpe.parm')
    sub_vpd_parm_files = f'{sub_common_parm_file},{sub_vpd_parm_file}'
    sub_vpe_parm_files = f'{sub_common_parm_file},{sub_vpe_parm_file}'
    ardupilot_dir = Path.home() / 'ardupilot'
    ardusub_path = ardupilot_dir / 'build/sitl/bin/ardusub'
    

    orca_bringup_dir = get_package_share_directory(
        'orca_bringup'
    )

    orb_settings_file = os.path.join(
        orca_bringup_dir,
        'param',
        'sim.yaml',
    )

    actions = []

    # Shared Gazebo -> ROS odometry bridge
    odometry_bridge_args = [
        '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'
    ]

    for i in range(n):

        robot_name = f'robot_{i}'

        # ------------------------------------------------------------------
        # Camera bridge
        # ------------------------------------------------------------------

        camera_topic = f'/{robot_name}/image_raw'

        actions.append(
            Node(
                package='ros_gz_image',
                executable='image_bridge',
                name=f'image_bridge_{robot_name}',
                namespace=robot_name,
                output='screen',
                arguments=[camera_topic],
                parameters=[
                    {
                        'use_sim_time': True
                    }
                ],
            )
        )

        # ------------------------------------------------------------------
        # Odometry bridge
        # ------------------------------------------------------------------

        odometry_bridge_args.append(
            f'/model/{robot_name}/odometry'
            '@nav_msgs/msg/Odometry[gz.msgs.Odometry'
        )

        # ------------------------------------------------------------------
        # Camera info
        # ------------------------------------------------------------------

        actions.append(
            Node(
                package='orca_bridge',
                executable='camera_info_publisher.py',
                name=f'camera_info_publisher_{robot_name}',
                namespace=robot_name,
                output='screen',
                parameters=[
                    {
                        'camera_info_url':
                            f'file://{camera_info_url}',

                        'frame_id':
                            f'{robot_name}/camera_sensor',
                    }
                ],
            )
        )

        # ------------------------------------------------------------------
        # base_link -> camera_link TF
        # ------------------------------------------------------------------

        actions.append(
            Node(
                package='tf2_ros',
                executable='static_transform_publisher',
                name=f'camera_tf_{robot_name}',
                namespace=robot_name,
                output='screen',
                parameters=[
                    {
                        'use_sim_time': True
                    }
                ],
                arguments=[
                    '--x', '0',
                    '--y', '0',
                    '--z', '0',
                    '--roll', '0',
                    '--pitch',
                    '1.5707963267948966',
                    '--yaw', '0',

                    '--frame-id',
                    f'{robot_name}/base_link',

                    '--child-frame-id',
                    f'{robot_name}/camera_link',
                ],
            )
        )

        # ------------------------------------------------------------------
        # ORB-SLAM3
        # ------------------------------------------------------------------

        actions.append(
            Node(
                package='orb_slam3_ros',
                executable='orb_slam3_ros_mono',
                name=f'orb_slam3_{robot_name}',
                namespace=robot_name,
                output='screen',
                parameters=[
                    {
                        'use_sim_time':
                            True,

                        'settings_file':
                            orb_settings_file,

                        'world_frame_id':
                            f'{robot_name}/world',
                    }
                ],
                remappings=[
                    (
                        '/image_raw',
                        f'/{robot_name}/image_raw'
                    ),
                ],
                condition=IfCondition(
                    LaunchConfiguration('orb')
                ),
            )
        )

        # ------------------------------------------------------------------
        # SLAM -> ArduSub MAVLink bridge
        # ------------------------------------------------------------------

        actions.append(
            Node(
                package='orca_bridge',
                executable='slam_bridge.py',
                name=f'slam_bridge_{robot_name}',
                namespace=robot_name,
                output='screen',
                parameters=[
                    {
                        'use_sim_time':
                            True,

                        'mav_device':
                            f'udpin:0.0.0.0:{14550 + i}',

                        'robot_name':
                            robot_name,

                        'use_vpe':
                            True,
                    }
                ],
                condition=IfCondition(
                    LaunchConfiguration('bridge')
                ),
            )
        )
        # Ardusub
        actions.append(
            ExecuteProcess(
                    cmd=[
                        str(ardusub_path),
                        '-S',
                        '--wipe',
                        '-M',
                        'JSON',
                        f'-I{i}',
                        '--home',
                        '47.6302,-122.3982391,-0.1,0',
                        '--defaults',
                        sub_vpe_parm_files,
                    ],
                    output='screen',
                    # condition=IfCondition(LaunchConfiguration('ardusub')),
                )
                )

    # ----------------------------------------------------------------------
    # One shared odometry + clock bridge
    # ----------------------------------------------------------------------

    actions.append(
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            name='odometry_bridge',
            output='screen',
            arguments=odometry_bridge_args,
        )
    )
    

    return actions


# ---------------------------------------------------------------------------
# Launch description
# ---------------------------------------------------------------------------

def generate_launch_description():

    ros_gz_sim = get_package_share_directory('ros_gz_sim')

    # -----------------------------------------------------------------------
    # Arguments
    # -----------------------------------------------------------------------

    number_arg = DeclareLaunchArgument(
        'number',
        default_value='1',
        description='Number of BlueROV2 robots',
    )

    camera_info_url_arg = DeclareLaunchArgument(
        'camera_info_url',
        default_value=os.path.join(
            get_package_share_directory(
                'bluerov2_description'
            ),
            'config',
            'sim_camera.yaml',
        ),
        description='Path to camera_info YAML',
    )

    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='True',
        description='Use Gazebo simulation time',
    )

    bridge_arg = DeclareLaunchArgument(
        'bridge',
        default_value='True',
        description='Launch SLAM MAVLink bridge',
    )

    orb_arg = DeclareLaunchArgument(
        'orb',
        default_value='True',
        description='Launch ORB-SLAM3',
    )

    use_vpe_arg = DeclareLaunchArgument(
        'use_vpe',
        default_value='True',
        description=(
            'Use VISION_POSITION_ESTIMATE instead of '
            'VISION_POSITION_DELTA'
        ),
    )

    # -----------------------------------------------------------------------
    # Gazebo resource paths
    # -----------------------------------------------------------------------

    bluerov2_description = get_package_share_directory(
        'bluerov2_description'
    )

    bluerov2_description_prefix = get_package_prefix(
        'bluerov2_description'
    )

    models_path = (
        os.path.join(
            bluerov2_description,
            'models'
        )
        + os.pathsep
        + os.path.join(
            bluerov2_description_prefix,
            'share'
        )
    )

    worlds_path = os.path.join(
        bluerov2_description,
        'worlds'
    )

    set_env_vars_resources = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=models_path,
    )

    add_env_vars_resources = AppendEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=worlds_path,
    )

    # -----------------------------------------------------------------------
    # Generate models
    # -----------------------------------------------------------------------

    generate_models = OpaqueFunction(
        function=spawn_n_robots
    )

    # -----------------------------------------------------------------------
    # Generate world + start Gazebo server
    # -----------------------------------------------------------------------

    generate_world_action = OpaqueFunction(
        function=generate_world
    )

    # -----------------------------------------------------------------------
    # Gazebo GUI
    # -----------------------------------------------------------------------

    gzclient = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                ros_gz_sim,
                'launch',
                'gz_sim.launch.py',
            )
        ),
        launch_arguments={
            'gz_args': '-g -v4',
        }.items(),
    )

    # -----------------------------------------------------------------------
    # RVIZ 
    # -----------------------------------------------------------------------

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        output='screen',
        parameters=[
            {
                'use_sim_time': True,
            }
        ],
        arguments=['-d', os.path.join(get_package_share_directory('orca_bringup'), 'rviz', 'sim.rviz')],
    )
    # -----------------------------------------------------------------------
    # Clock bridge
    # -----------------------------------------------------------------------

    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='clock_bridge',
        output='screen',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'
        ],
    )

    # -----------------------------------------------------------------------
    # Perception + SLAM
    # -----------------------------------------------------------------------

    perception_and_slam = OpaqueFunction(
        function=launch_perception_and_slam
    )



    # -----------------------------------------------------------------------
    # LaunchDescription
    # -----------------------------------------------------------------------

    ld = LaunchDescription()

    ld.add_action(set_env_vars_resources)
    ld.add_action(add_env_vars_resources)

    ld.add_action(number_arg)
    ld.add_action(camera_info_url_arg)
    ld.add_action(use_sim_time_arg)
    ld.add_action(bridge_arg)
    ld.add_action(orb_arg)
    ld.add_action(use_vpe_arg)

    ld.add_action(generate_models)
    ld.add_action(generate_world_action)

    ld.add_action(gzclient)

    ld.add_action(clock_bridge)

    ld.add_action(perception_and_slam)
    ld.add_action(rviz)

    return ld