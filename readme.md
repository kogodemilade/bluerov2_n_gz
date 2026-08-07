BlueRov2_GZ

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

**Usage**

The key command is:

ros2 launch bluerov2_description bluerov2.launch.py number:={n}

where n is replaced with the number of robots you may want to spawn. It defaults to 1, in which case, you may leave the number argument out completely.

*Notes:*
Gazebo caches data, which make running subsequent launches with different numbers of n prone to unpredictable behaviour. So, after each run these commands:
```
rm -rf build install log generated_models 
rm world.sdf
rm -rf ~/.gz/fuel
rm -rf ~/.gz/sim
pkill -f gz
pkill -f ruby
colcon build
```
(you can copy all at once and paste into your terminal.)
This ensures no gazebo process is still running, and that all its cached has been wiped. It's only necessary if you want to spawn a number of bots different from the one that was just closed. It also doesn't take so long (within 2 seconds usually).
This has not been stress-tested, so some issues may still arise. Please feel free to raise issues.
