from launch import LaunchDescription
from launch_ros.actions import Node, SetParameter
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable, IncludeLaunchDescription, AppendEnvironmentVariable, LogInfo, OpaqueFunction
from ros_gz_bridge.actions import RosGzBridge
import os
from ament_index_python import get_package_share_directory, get_package_prefix
from launch_ros.parameter_descriptions import ParameterValue 
from launch.substitutions import Command, LaunchConfiguration, EnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from jinja2 import Environment, FileSystemLoader
from pathlib import Path


def spawn_n_robots(context, *args, **kwargs):
    n = int(LaunchConfiguration('number').perform(context))

    actions = []
    share_dir = get_package_share_directory("bluerov2_description")
    env = Environment(loader=FileSystemLoader(Path(share_dir)/ "models" / "bluerov2"))
    template = env.get_template("model.sdf.jinja")
    base_dir = Path("~/bluerov2_n_gz").expanduser()
    models_dir = base_dir / "generated_models"
    models_dir.mkdir(parents=True, exist_ok=True)
    config_template = env.get_template("model.config.jinja")

    for i in range(n):
        robot = {
            "name": f"robot_{i}",
            "namespace":f"robot_{i}",
            "fdm_port" : 9002 + i,
            "mavlink_port":14550+i,
            "x" : i*5,
            "y":0,
            "z":-2,
        }
        rendered = template.render(
            robot=robot
        )
        robot_dir = models_dir / f"robot_{i}"
        robot_dir.mkdir(parents=True, exist_ok=True)
        rendered_file = robot_dir / f"model.sdf"
        with open(rendered_file, 'w') as f:
            f.write(rendered)

        config = config_template.render(robot=robot)
        with open(robot_dir / "model.config", 'w') as f:
            f.write(config)

    actions.append(
        AppendEnvironmentVariable(
            name='GZ_SIM_RESOURCE_PATH',
            value=str(models_dir)
        )
    )
    return actions


def create_n_model_names(context, ros_gz_sim, *args, **kwargs):
    n = int(LaunchConfiguration('number').perform(context))

    actions = []
    robot_names = []
    share_dir = get_package_share_directory("bluerov2_description")
    env = Environment(loader=FileSystemLoader(Path(share_dir)/ "worlds"))
    template = env.get_template("bluerov2_underwater.world.jinja")

    for i in range(n):
        robot_dict = {"name": f"robot_{i}",
                      "x": i*2,}
        robot_names.append(robot_dict)
    rendered = template.render(
        robot_names=robot_names
    )
    rendered_file = Path("~/bluerov2_n_gz").expanduser() / f"world.sdf"
    with open(rendered_file, 'w') as f:
        f.write(rendered)

    gzserver_cmd = IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(ros_gz_sim, "launch", "gz_sim.launch.py")
                ),
                launch_arguments={'gz_args': ['-r -s -v4 ', rendered_file], 'on_exit_shutdown': 'true'}.items()
    )
    actions.append(gzserver_cmd)

    return actions

def generate_launch_description():
    sim_time_parameter = SetParameter(name='use_sim_time', value=True)
    bluerov2_description = get_package_share_directory("bluerov2_description")
    bluerov2_description_prefix = get_package_prefix("bluerov2_description")

    ros_gz_sim = get_package_share_directory("ros_gz_sim")

    models_path = os.path.join(bluerov2_description, 'models') + os.pathsep + os.path.join(bluerov2_description_prefix, "share")
    worlds_path = os.path.join(bluerov2_description, 'worlds')

    model_file = os.path.join(bluerov2_description, "models", "bluerov2", "model.sdf")

    set_env_vars_resources = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=models_path) 

    add_env_vars_resources = AppendEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=worlds_path) 

    number_arg = DeclareLaunchArgument(
            name="number",
            default_value="1",
            description="number of robots to spawn" 
            )

    world = OpaqueFunction(function=create_n_model_names, args=[ros_gz_sim])
    
    gzclient_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
            launch_arguments={'gz_args': '-g -v4 '}.items()
    )
    
    clock_bridge = Node(
    package='ros_gz_bridge',
    executable='parameter_bridge',
    name='clock_bridge',
    output='screen',
    arguments=[
        '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'
    ],
)
    
    log_model_path = LogInfo(
        condition=None,
        msg=EnvironmentVariable('GZ_SIM_RESOURCE_PATH')
    )

    spawn_robots = OpaqueFunction(function=spawn_n_robots)

    ld = LaunchDescription()
    ld.add_action(number_arg)
    ld.add_action(sim_time_parameter)
    ld.add_action(set_env_vars_resources)
    ld.add_action(add_env_vars_resources)
    ld.add_action(spawn_robots)
    ld.add_action(world)
    ld.add_action(gzclient_cmd)
    ld.add_action(clock_bridge)
    ld.add_action(log_model_path)
    

    return ld