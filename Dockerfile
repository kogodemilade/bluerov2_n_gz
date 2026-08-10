# ============================================================
# BlueROV2_n_gz development/simulation environment
#
# Intended ROS distribution: Jazzy
# Host ROS distribution does not matter when running the
# complete simulation inside this container.
# ============================================================

FROM osrf/ros:jazzy-desktop

SHELL ["/bin/bash", "-c"]

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

# ============================================================
# Basic build/runtime tools
# ============================================================

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
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# ============================================================
# ROS 2 / Gazebo dependencies
# ============================================================

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

# ============================================================
# GStreamer / ArduPilot dependencies
# ============================================================

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

# ============================================================
# Gazebo package repository
# ============================================================

RUN curl -fsSL \
    https://packages.osrfoundation.org/gazebo.gpg \
    -o /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg \
    && echo \
    "deb [arch=$(dpkg --print-architecture) \
    signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] \
    https://packages.osrfoundation.org/gazebo/ubuntu-stable \
    $(lsb_release -cs) main" \
    > /etc/apt/sources.list.d/gazebo-stable.list

RUN wget \
    https://raw.githubusercontent.com/osrf/osrf-rosdep/master/gz/00-gazebo.list \
    -O /etc/ros/rosdep/sources.list.d/00-gazebo.list

# ============================================================
# rosdep
# ============================================================

RUN rosdep init 2>/dev/null || true
RUN rosdep update

# ============================================================
# Clone repository WITH submodules
#
# This avoids relying on .git being present in the Docker
# build context.
#
# .gitmodules contains:
#   orca5
#   src/orb_slam3_ros
# ============================================================

WORKDIR /workspace

RUN git clone --recurse-submodules \
    https://github.com/kogodemilade/bluerov2_n_gz.git \
    /workspace/bluerov2_n_gz

WORKDIR /workspace/bluerov2_n_gz

# Make absolutely sure nested submodules are initialized.
RUN git submodule update --init --recursive

# ============================================================
# ORB-SLAM3 vocabulary
# ============================================================

WORKDIR /workspace/bluerov2_n_gz/src/orb_slam3_ros/modules/ORB_SLAM3/Vocabulary

RUN if [ -f ORBvoc.txt.tar.gz ]; then \
        tar -xzf ORBvoc.txt.tar.gz; \
    fi

# ============================================================
# Make orca_msgs available as a normal ROS package
#
# ORCA5 contains orca_msgs, while this workspace needs to
# discover it from src/.
# ============================================================

RUN rm -rf /workspace/bluerov2_n_gz/src/orca_msgs \
    && cp -a \
    /workspace/bluerov2_n_gz/orca5/orca_msgs \
    /workspace/bluerov2_n_gz/src/orca_msgs

# ============================================================
# Python virtual environment
#
# No --break-system-packages is required because all pip
# packages go into this virtual environment.
# ============================================================

WORKDIR /workspace/bluerov2_n_gz

RUN python3 -m venv /workspace/bluerov2_n_gz/.venv \
    --system-site-packages

ENV PATH="/workspace/bluerov2_n_gz/.venv/bin:$PATH"

RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir \
        geopy \
        pymavlink \
        mavproxy \
        future \
        transforms3d \
        jinja2

# ============================================================
# ArduPilot / ArduSub SITL
# ============================================================

WORKDIR /workspace

RUN git clone https://github.com/ArduPilot/ardupilot.git

WORKDIR /workspace/ardupilot

# Keep the known-compatible commit from the previous Dockerfile.
ARG ARDUPILOT_COMMIT=e5e97094

RUN git checkout ${ARDUPILOT_COMMIT} \
    && git submodule update --init --recursive

ENV SKIP_AP_EXT_ENV=1
ENV SKIP_AP_GRAPHIC_ENV=1
ENV SKIP_AP_COV_ENV=1
ENV SKIP_AP_GIT_CHECK=1

# Install ArduPilot build dependencies.
RUN Tools/environment_install/install-prereqs-ubuntu.sh -y

# Build only ArduSub SITL.
RUN ./modules/waf/waf-light configure --board sitl \
    && ./modules/waf/waf-light build --target bin/ardusub

# ============================================================
# GeographicLib datasets
#
# Use the copy shipped by the repository if available.
# ============================================================

RUN if [ -f /workspace/bluerov2_n_gz/install_geographiclib_datasets.sh ]; then \
        chmod +x /workspace/bluerov2_n_gz/install_geographiclib_datasets.sh \
        && /workspace/bluerov2_n_gz/install_geographiclib_datasets.sh; \
    fi

# ============================================================
# ardupilot_gazebo
# ============================================================

WORKDIR /workspace

RUN git clone https://github.com/ArduPilot/ardupilot_gazebo.git

WORKDIR /workspace/ardupilot_gazebo

# Keep the known-compatible commit from the previous Dockerfile.
ARG ARDUPILOT_GAZEBO_COMMIT=cc0290d

RUN git checkout ${ARDUPILOT_GAZEBO_COMMIT}

ENV GZ_VERSION=harmonic

RUN mkdir -p build \
    && cd build \
    && cmake .. -DCMAKE_BUILD_TYPE=RelWithDebInfo \
    && make -j"$(nproc)"

# ============================================================
# Gazebo / ArduPilot runtime environment
# ============================================================

ENV GZ_SIM_SYSTEM_PLUGIN_PATH=/workspace/ardupilot_gazebo/build

ENV GZ_SIM_RESOURCE_PATH=/workspace/bluerov2_n_gz/src/bluerov2_description/models:/workspace/bluerov2_n_gz/src/bluerov2_description/worlds

ENV PATH="/workspace/ardupilot/build/sitl/bin:${PATH}"

# ============================================================
# Verify important executables during image build
# ============================================================

RUN gz sim --version \
    && test -x /workspace/ardupilot/build/sitl/bin/ardusub \
    && test -f /workspace/ardupilot_gazebo/build/libArduPilotPlugin.so

# ============================================================
# Build ROS workspace
# ============================================================

WORKDIR /workspace/bluerov2_n_gz

RUN source /opt/ros/jazzy/setup.bash \
    && rosdep install \
        --from-paths src \
        --ignore-src \
        --rosdistro jazzy \
        -r -y \
    && colcon build --symlink-install

# ============================================================
# Interactive shell configuration
# ============================================================

RUN echo 'source /opt/ros/jazzy/setup.bash' >> /root/.bashrc \
    && echo 'source /workspace/bluerov2_n_gz/.venv/bin/activate' >> /root/.bashrc \
    && echo 'source /workspace/bluerov2_n_gz/install/setup.bash 2>/dev/null || true' >> /root/.bashrc \
    && echo 'export GZ_VERSION=harmonic' >> /root/.bashrc \
    && echo 'export GZ_SIM_SYSTEM_PLUGIN_PATH=/workspace/ardupilot_gazebo/build:${GZ_SIM_SYSTEM_PLUGIN_PATH}' >> /root/.bashrc \
    && echo 'export GZ_SIM_RESOURCE_PATH=/workspace/bluerov2_n_gz/src/bluerov2_description/models:/workspace/bluerov2_n_gz/src/bluerov2_description/worlds:${GZ_SIM_RESOURCE_PATH}' >> /root/.bashrc \
    && echo 'export PATH=/workspace/ardupilot/build/sitl/bin:$PATH' >> /root/.bashrc

# ============================================================
# Default working directory
# ============================================================

WORKDIR /workspace/bluerov2_n_gz

ENTRYPOINT ["/bin/bash"]
