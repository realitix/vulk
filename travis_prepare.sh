#!/usr/bin/env bash

# Download Vulkan SDK
wget https://vulkan.lunarg.com/sdk/download/1.0.46.0/linux/vulkansdk-linux-x86_64-1.0.46.0.run
chmod u+x vulkansdk-linux-x86_64-1.0.46.0.run
./vulkansdk-linux-x86_64-1.0.46.0.run
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$DIR/VulkanSDK/1.0.46.0/x86_64/lib/
export VK_LAYER_PATH=$DIR/VulkanSDK/1.0.46.0/x86_64/etc/explicit_layer.d
