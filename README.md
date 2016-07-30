# VULK - Vulkan 3d engine

## What is it ?

Vulk is a 3d engine aimed to provide the best graphical experience with Vulkan API.
It is written in Python with C binding and is based on SDL2.

## What is the project goal ?

- Easy to use: you don't need to understand Vulkan to use VULK.
- Modular: every single part of the api must be modular.
- Full: you shouldn't need to customize core code, it should suits everyone needs.

## Why this project ?

Currently it's just a hobby project but it could become something big one day.

## Architecture

```
vulk/
    graphic/
        renderer/
            vulkan/
            webgl/
            opengl/
        d3/
            material/
            core/
        d2/

```

## How it works

It's similar to LibGDX because I like their 3D API.

```
scene = Scene()
camera = PerspectiveCamera()
renderer = VulkanRenderer()
renderer.render(scene, camera)
```
