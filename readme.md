**BlueRov2_n_gz**

The name bluerov2_n_gz is just a horrible name, not much meaning to it asides the fact that it was supposed to signify that it can launch an arbitrary number (n) bots in the same world.

This was designed on Ubuntu 24.04 LTS, with ROS@ jazzy. Due to the incorporation of orca5 features, this may not run on versions older than jazzy. The best thing to do would be to create a dockerized jazzy container. Documentation would come in later.

If you're getting errors, the first thing to check are the directories. A few things are currently hardcoded due to debugging/testing. But the quick fix may be to move this project to home (\~/bluerov2_n_gz). If you've not cloned it yet, cloning in home directory is best. To clarify, the home directory (\~) expands to \~/{user} where user is the name of your profile. For example, \~/demi. This will be fixed in a future release to allow more flexibility.

**Setup**

This repository contains submodules.  Therefore, the cloning command is:
```
git clone --recurse-submodules https://github.com/kogodemilade/bluerov2_n_gz.git
```

after cloning repository, run:
```
cd ~/bluerov2_n_gz
colcon build
source install/setup.bash
```

This requires jinja2 and transformations3D installed, and can be installed via pip (this should be ran in the project's root directory, /bluerov2_n_gz: 

1) Source python environment
```
python3 -m venv .venv
source .venv/bin/activate
```

2) install jinja
```
pip install jinja2
pip install transformations3d
```

3) deactivate environment
```
deactivate
```

**ArduSub**

Ardupilot should be installed if not already. Installation instructions can be found [here](https://ardupilot.org/dev/docs/building-setup-linux.html).



**Usage**
The key command is:
```
ros2 launch bluerov2_description bluerov2.launch.py number:={n}
```

where n is replaced with the number of robots you may want to spawn. It defaults to 1, in which case, you may leave the number argument out completely.
This requires ros to be sourced, as well as your pip environment.

*Notes:*
Gazebo caches data, which make running subsequent launches with different numbers of n prone to unpredictable behaviour. So, after each launch, run these commands:
```
rm -rf ~/.gz/fuel
rm -rf ~/.gz/sim
colcon build --packages-select bluerov2_description
```
(you can copy all at once and paste into your terminal.)
This ensures all gazebo's cached data has been wiped. It's only necessary if you want to spawn a number of bots different from the one that was just closed. It also doesn't take so long (within 2 seconds usually).
This has not been stress-tested, so some issues may still arise. Please feel free to raise issues.


The description file also launches ardusub instances using ardupilot and ardupilot_gazebo. Due to mavproxy's interavtive nature, I believed it best to exclude this from the launch file. Therefore, for each bot, you'd need a separate terminal window to launch mavproxy which sends commands to the robot. This is a deliberate design decision.

In a new terminal, source ardupilot and launch mavproxy
```
. /home/<user>/venv-ardupilot/bin/activate
mavproxy.py --master=tcp:127.0.01:5760 --out=udp:127.0.0.1:14550
```

For successive mavproxy launches, the tcp port increases by 10 (5770, 5780, etc). The udp port increases by 1 (14551, 14552) etc. 
This ensures each terminal instance matches a unique bluerov2 robot. I suggest terminator for stacking multiple terminal instances in the same window.

In the same terminal as the previous command, the throttle can be armed and commands to the respective robots can be sent. To arm the throttle:

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

**Rviz**

The launch file also launches rviz, but the tf transforms are published by the slam nodes, which don't activate until the bots are sufficiently close the seafloor. In this case, after arming the throttle, send an rc 3 command with a pwm value between 1000 and 1500 (this commands the robot to move downwards). I find the best way to know how close is 'close enough' is by adding the 'image display' in gazebo till the camera starts to show an image. Sometimes, even when close to the seafloor, it may still not start slam, due to the lack of features. When done, 'rc 3 1500' command should be sent to hold in that position. Sometimes due to the featureless environment, The command 'rc 5 1550' should be sent, which moves the robot forward. Afterwhich, the map usually starts being generated, and the transforms get published. The transform and pointcloud should show shortly after.  
