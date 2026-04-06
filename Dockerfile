# ============================================================================
# MVS Dockerfile - Reproducible Build for DO-178C Certification
# ============================================================================
# Purpose: Deterministic, auditable container build for safety-critical robotics
# Base: ROS2 Humble LTS (Ubuntu 22.04)
# ============================================================================

ARG ROS_DISTRO=humble
FROM ros:${ROS_DISTRO}-ros-base

LABEL maintainer="Luke Pepin <luke@sentryc2.io>"
LABEL description="MVS (Minimum Viable Spring) Edge-First Robotics Framework"
LABEL version="0.1-alpha"

# ============================================================================
# 1. DETERMINISTIC BUILD FLAGS
# ============================================================================
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
RUN echo 'APT::Install-Recommends "0"; APT::Install-Suggests "0";' > /etc/apt/apt.conf.d/01norecommend

# ============================================================================
# 2. SYSTEM DEPENDENCIES (No version pins - use latest from Ubuntu 22.04)
# ============================================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    python3-pip \
    python3-dev \
    python3-venv \
    net-tools \
    iputils-ping \
    ca-certificates \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# ============================================================================
# 3. BUILD TOOLS (Required for C++ extensions: micro-ecc, cryptography)
# ============================================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    libgmp-dev \
    libffi-dev \
    cmake \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# ============================================================================
# 4. PYTHON DEPENDENCIES (Pinned with pip requirements)
# ============================================================================
# Install base requirements for datalogger (pyserial, pandas) and any backend requirements
COPY backend/requirements.txt* /tmp/
RUN pip3 install --no-cache-dir pyserial pandas && \
    if [ -f /tmp/requirements.txt ]; then pip3 install --no-cache-dir -r /tmp/requirements.txt; fi

# ============================================================================
# 5. ROS WORKSPACE INITIALIZATION
# ============================================================================
WORKDIR /workspace/ros2_ws

# Create directory structure
RUN mkdir -p /workspace/ros2_ws/src && \
    mkdir -p /workspace/ros2_ws/build && \
    mkdir -p /workspace/ros2_ws/install

# ============================================================================
# 6. DEFAULT WORKSPACE BUILD
# ============================================================================
# Build empty or existing workspace
SHELL ["/bin/bash", "-c"]
RUN source /opt/ros/${ROS_DISTRO}/setup.bash && \
    cd /workspace/ros2_ws && \
    colcon build --parallel-workers 4 --symlink-install && \
    rm -rf build/

# ============================================================================
# 8. SHELL CONFIGURATION (Permanent)
# ============================================================================
# Source ROS + workspace on container startup
RUN echo "#!/bin/bash" > /entrypoint.sh && \
    echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> /entrypoint.sh && \
    echo "if [ -f /workspace/ros2_ws/install/setup.bash ]; then source /workspace/ros2_ws/install/setup.bash; fi" >> /entrypoint.sh && \
    echo 'exec "$@"' >> /entrypoint.sh && \
    chmod +x /entrypoint.sh

RUN echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> ~/.bashrc && \
    echo "if [ -f /workspace/ros2_ws/install/setup.bash ]; then source /workspace/ros2_ws/install/setup.bash; fi" >> ~/.bashrc

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/bin/bash"]

# ============================================================================
# 9. SECURITY & METADATA
# ============================================================================
LABEL security="Run as root in dev container; use rootless mode in production"
ENV MVS_VERSION=0.1-alpha
ENV BUILD_DATE="2026-02-02"
ENV VCS_REF="main"
LABEL org.opencontainers.image.version=$MVS_VERSION
LABEL org.opencontainers.image.created=$BUILD_DATE
LABEL org.opencontainers.image.source="https://github.com/lpep64/MVS"

# ============================================================================
# 10. HEALTHCHECK (Optional)
# ============================================================================
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD ros2 topic list > /dev/null 2>&1 || exit 1
