BlueRov2_n_gz

The name bluerov2_n_gz is just a horrible name, not much meaning to it asides the fact that it was supposed to signify that it can launch an arbitrary number (n) bots in the same world.

This was designed on Ubuntu 22.04 LTS, with ROS@ jazzy. This is just a launch file so there shouldn't be many errors in other ROS2 versions asides variable name issues and other trivial issues.

If you're getting errors, the first thing to check are the directories. A few things are currently hardcoded due to debugging/testing. But the quick fix may be to move this project to home (\~/bluerov2_n_gz). If you've not cloned it yet, cloning in home directory is best. To clarify, the home directory (\~) expands to \~/{user} where user is the name of your profile. For example, \~/demi. This will be fixed in a future release to allow more flexibility.

**Setup**

after cloning repository, run:
```
cd ~/bluerov2_n_gz
colcon build
source install/setup.bash
```

Thhis also requires jinja2 installed, and can be installed via pip (this should be ran in the project's root directory, /bluerov2_n_gz: 

1) Source python environment
```
python3 -m venv .venv
source .venv/bin/activate
```

2) install jinja
```
pip install jinja2
```

3) deactivate environment
```
deactivate
```


**Usage**

The key command is:

ros2 launch bluerov2_description bluerov2.launch.py number:={n}

where n is replaced with the number of robots you may want to spawn. It defaults to 1, in which case, you may leave the number argument out completely.

*Notes:*
Gazebo caches data, which make running subsequent launches with different numbers of n prone to unpredictable behaviour. So, after each run these commands:
```
rm -rf ~/.gz/fuel
rm -rf ~/.gz/sim
colcon build
```
(you can copy all at once and paste into your terminal.)
This ensures no gazebo process is still running, and that all its cached has been wiped. It's only necessary if you want to spawn a number of bots different from the one that was just closed. It also doesn't take so long (within 2 seconds usually).
This has not been stress-tested, so some issues may still arise. Please feel free to raise issues.


**ArduSub**

Ardupilot should be installed if not already. Installation instructions can be found [here](https://ardupilot.org/dev/docs/building-setup-linux.html). After installing and building, the following code expects you are in a separate terminal and in the /ardupilot directory.

Each Ardusub instance must be run in a seperate terminal.
```
Tools/autotest/sim_vehicle.py -I0 -L RATBeach -v ArduSub --model=JSON --out=udp:0.0.0.0:14550 --console
```

-I0 indicates that this is the first instance. For subsequent instances, it naturally follows -I1, -I2, ..., -In-1 for n instances.
Afterwhich, the throttle can be armed and commands to the respective robots can be sent. To arm the throttle:

```
arm throttle
```

(Arming the throttle is required before any commands are sent)

Sending commands:
```
rc x y
```
x is a variable representing the channel (between 1 - 16 I believe, but 3 is confirmed vertical movement, while 5 is lateral Y-axis movement. This will be updated).
and y represents the PWM inputs, between 1000 and 2000. 

*Example*
```
rc 3 1300
```
