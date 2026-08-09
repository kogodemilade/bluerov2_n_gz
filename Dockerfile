FROM osrf/ros:jazzy-desktop

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

SHELL ["/bin/bash", "-c"]

# ------------------------------------------------------------
# Basic tools
# ------------------------------------------------------------

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    git-lfs \
    wget \
    curl \
    sudo \
    vim \
    nano \
    python3-pip \
    python3-venv \
    python3-dev \
    python3-colcon-common-extensions \
    python3-vcstool \
    python3-rosdep \
    pkg-config \
    libopencv-dev \
    libeigen3-dev \
    libgl1 \
    libglvnd0 \
    libglx0 \
    libegl1 \
    libx11-6 \
    libxext6 \
    rapidjson-dev \
    xterm \
    && rm -rf /var/lib/apt/lists/*


# ------------------------------------------------------------
# ROS / Gazebo dependencies
# ------------------------------------------------------------

RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-jazzy-ros-gz \
    ros-jazzy-rviz2 \
    ros-jazzy-tf2 \
    ros-jazzy-tf2-ros \
    ros-jazzy-tf2-tools \
    ros-jazzy-nav-msgs \
    ros-jazzy-sensor-msgs \
    ros-jazzy-geometry-msgs \
    ros-jazzy-std-srvs \
    ros-jazzy-launch \
    ros-jazzy-launch-ros \
    ros-jazzy-ament-index-python \
    && rm -rf /var/lib/apt/lists/*


# ------------------------------------------------------------
# GStreamer / ArduPilot dependencies
# ------------------------------------------------------------

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    gstreamer1.0-gl \
    gstreamer1.0-tools \
    python3-wxgtk4.0 \
    && rm -rf /var/lib/apt/lists/*


# ------------------------------------------------------------
# Gazebo OSRF repository
# Needed by ardupilot_gazebo
# ------------------------------------------------------------

RUN curl -fsSL \
    https://packages.osrfoundation.org/gazebo.gpg \
    -o /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] https://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" \
    > /etc/apt/sources.list.d/gazebo-stable.list

RUN wget \
    https://raw.githubusercontent.com/osrf/osrf-rosdep/master/gz/00-gazebo.list \
    -O /etc/ros/rosdep/sources.list.d/00-gazebo.list


# ------------------------------------------------------------
# rosdep
# ------------------------------------------------------------

RUN rosdep init 2>/dev/null || true
RUN rosdep update


# ------------------------------------------------------------
# Workspace
# ------------------------------------------------------------

WORKDIR /workspace

COPY . /workspace/bluerov2_n_gz

WORKDIR /workspace/bluerov2_n_gz


# ------------------------------------------------------------
# Make sure submodules are initialized
# ------------------------------------------------------------

RUN git submodule update --init --recursive


# ------------------------------------------------------------
# ORB-SLAM3 vocabulary
# ------------------------------------------------------------

WORKDIR /workspace/bluerov2_n_gz/src/orb_slam3_ros/modules/ORB_SLAM3/Vocabulary

RUN if [ -f ORBvoc.txt.tar.gz ]; then \
        tar -xvf ORBvoc.txt.tar.gz; \
    fi


# ------------------------------------------------------------
# orca_msgs
#
# The repository uses the modified orca_bridge under src/,
# but orca_msgs lives in the orca5 submodule.
# Colcon will not automatically discover it there.
# ------------------------------------------------------------

RUN cp -r \
    /workspace/bluerov2_n_gz/orca5/orca_msgs \
    /workspace/bluerov2_n_gz/src/orca_msgs


# ------------------------------------------------------------
# Python dependencies used by Orca5 / bridge
#
# Orca5 requirements:
# geopy
# pymavlink
# mavproxy
# future
# transforms3d
#
# Your repository additionally requires Jinja2.
# ------------------------------------------------------------

WORKDIR /workspace/bluerov2_n_gz

RUN python3 -m venv /workspace/bluerov2_n_gz/.venv \
    --system-site-packages

RUN /workspace/bluerov2_n_gz/.venv/bin/pip install --no-cache-dir \
    geopy \
    pymavlink \
    mavproxy \
    future \
    transforms3d \
    jinja2


# ------------------------------------------------------------
# ArduPilot / ArduSub
# ------------------------------------------------------------

WORKDIR /workspace

RUN git clone https://github.com/ArduPilot/ardupilot.git

WORKDIR /workspace/ardupilot

RUN git checkout e5e97094 \
    && git submodule update --init --recursive

ENV SKIP_AP_EXT_ENV=1
ENV SKIP_AP_GRAPHIC_ENV=1
ENV SKIP_AP_COV_ENV=1
ENV SKIP_AP_GIT_CHECK=1

RUN Tools/environment_install/install-prereqs-ubuntu.sh -y

RUN python3 -m pip install --break-system-packages future

RUN ./modules/waf/waf-light configure --board sitl \
    && ./modules/waf/waf-light build --target bin/ardusub


# ------------------------------------------------------------
# ardupilot_gazebo
# ------------------------------------------------------------

WORKDIR /workspace

RUN git clone https://github.com/ArduPilot/ardupilot_gazebo.git \
    && cd ardupilot_gazebo \
    && git checkout cc0290d

ENV GZ_VERSION=harmonic

WORKDIR /workspace/ardupilot_gazebo

RUN mkdir -p build \
    && cd build \
    && cmake .. -DCMAKE_BUILD_TYPE=RelWithDebInfo \
    && make -j$(nproc)


# ------------------------------------------------------------
# Environment
# ------------------------------------------------------------

ENV GZ_SIM_SYSTEM_PLUGIN_PATH=/workspace/ardupilot_gazebo/build
ENV GZ_SIM_RESOURCE_PATH=/workspace/bluerov2_n_gz/src/bluerov2_description/models:/workspace/bluerov2_n_gz/src/bluerov2_description/worlds
ENV PATH=/workspace/ardupilot/build/sitl/bin:$PATH

RUN echo 'source /opt/ros/jazzy/setup.bash' >> /root/.bashrc \
    && echo 'source /workspace/bluerov2_n_gz/.venv/bin/activate' >> /root/.bashrc \
    && echo 'source /workspace/bluerov2_n_gz/install/setup.bash 2>/dev/null || true' >> /root/.bashrc \
    && echo 'export GZ_SIM_SYSTEM_PLUGIN_PATH=/workspace/ardupilot_gazebo/build' >> /root/.bashrc \
    && echo 'export PATH=/workspace/ardupilot/build/sitl/bin:$PATH' >> /root/.bashrc


# ------------------------------------------------------------
# Build ROS workspace
# ------------------------------------------------------------

WORKDIR /workspace/bluerov2_n_gz

RUN source /opt/ros/jazzy/setup.bash \
    && rosdep update \
    && rosdep install --from-paths src --ignore-src -r -y \
    && colcon build --symlink-install


# ------------------------------------------------------------
# Default shell
# ------------------------------------------------------------

ENTRYPOINT ["/bin/bash"]
