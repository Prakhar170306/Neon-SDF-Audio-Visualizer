# Neon SDF Visualizer

A real-time GPU shader-based audio reactive visualizer built using Python, OpenGL, GLSL, and Signed Distance Fields.

## Features

- Real-time GLSL shader rendering
- Signed Distance Field glowing ring
- Mouse-based interaction
- Audio-reactive visual bars
- Smooth animation using time uniforms
- 60 FPS rendering loop
- ESC key exit control
- FPS display in window title

## Tech Stack

- Python
- Pygame
- PyOpenGL
- GLSL
- NumPy
- SoundDevice

## Controls

- Move mouse: control glowing ring position
- Play music / speak: audio bars react
- ESC: exit application

## How to Run

Install dependencies:

```bash
py -3.13 -m pip install pygame PyOpenGL numpy sounddevice