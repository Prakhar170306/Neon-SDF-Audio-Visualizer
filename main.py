import time
import os
import pygame
import numpy as np
import sounddevice as sd
import miniaudio
from OpenGL.GL import *

pygame.init()

WIDTH, HEIGHT = 900, 520

MP3_FILE = "music.mp3.mp3"
AUDIO_MODE = "mp3"

FFT_BANDS = 64
fft_levels = np.zeros(FFT_BANDS, dtype=np.float32)
smooth_fft = np.zeros(FFT_BANDS, dtype=np.float32)

pygame.display.set_mode((WIDTH, HEIGHT), pygame.OPENGL | pygame.DOUBLEBUF)
glViewport(0, 0, WIDTH, HEIGHT)
pygame.display.set_caption("Neon SDF Visualizer")

clock = pygame.time.Clock()
start_time = time.time()

raw_audio = 0.0
smooth_audio = 0.0

bass = 0.0
mid = 0.0
treble = 0.0

smooth_bass = 0.0
smooth_mid = 0.0
smooth_treble = 0.0

theme = 1
glow_power = 1.0

MAX_PARTICLES = 32
particles = [{"x": 0.5, "y": 0.5, "life": 0.0} for _ in range(MAX_PARTICLES)]
particle_index = 0
last_spawn_time = 0.0

mp3_data = None
mp3_pos = 0
mp3_sample_rate = 44100
mp3_channels = 2
mp3_playing = True


def load_shader_file(path):
    with open(path, "r", encoding="utf-8") as file:
        return file.read()


def analyze_audio(audio_chunk):
    global raw_audio
    global bass
    global mid
    global treble
    global fft_levels

    MAX_AUDIO = 3.0

    if audio_chunk is None or len(audio_chunk) == 0:
        return

    mono = audio_chunk

    if len(mono.shape) > 1:
        mono = np.mean(mono, axis=1)

    mono = mono.astype(np.float32)

    rms = np.sqrt(np.mean(mono * mono))
    raw_audio = min(rms * 25.0, MAX_AUDIO)

    window = np.hanning(len(mono))
    spectrum = np.abs(np.fft.rfft(mono * window))
    spectrum = np.log1p(spectrum)

    usable = spectrum[1:512]

    if len(usable) < FFT_BANDS:
        padded = np.zeros(FFT_BANDS, dtype=np.float32)
        padded[:len(usable)] = usable
        usable = padded

    chunks = np.array_split(usable, FFT_BANDS)
    band_values = np.array([np.mean(chunk) for chunk in chunks], dtype=np.float32)

    max_value = np.max(band_values)
    if max_value > 0:
        band_values = band_values / max_value

    fft_levels = band_values.astype(np.float32)

    bass = float(np.mean(fft_levels[0:12]) * MAX_AUDIO)
    mid = float(np.mean(fft_levels[12:40]) * MAX_AUDIO)
    treble = float(np.mean(fft_levels[40:64]) * MAX_AUDIO)

    raw_audio = max(raw_audio, bass * 0.8, mid * 0.5, treble * 0.4)


def mic_callback(indata, frames, time_info, status):
    if AUDIO_MODE == "mic":
        analyze_audio(indata)


def load_mp3():
    global mp3_data
    global mp3_sample_rate
    global mp3_channels
    global AUDIO_MODE

    if not os.path.exists(MP3_FILE):
        print("MP3 not found. Mic mode active.")
        AUDIO_MODE = "mic"
        return

    decoded = miniaudio.decode_file(
        MP3_FILE,
        output_format=miniaudio.SampleFormat.FLOAT32
    )

    mp3_sample_rate = decoded.sample_rate
    mp3_channels = decoded.nchannels

    samples = np.array(decoded.samples, dtype=np.float32)
    mp3_data = samples.reshape(-1, mp3_channels)

    print("Loaded:", MP3_FILE)


def mp3_callback(outdata, frames, time_info, status):
    global mp3_pos

    if AUDIO_MODE != "mp3" or mp3_data is None or not mp3_playing:
        outdata[:] = np.zeros((frames, mp3_channels), dtype=np.float32)
        return

    end = mp3_pos + frames
    chunk = mp3_data[mp3_pos:end]

    if len(chunk) < frames:
        mp3_pos = 0
        chunk = mp3_data[mp3_pos:mp3_pos + frames]

        if len(chunk) < frames:
            missing = frames - len(chunk)
            silence = np.zeros((missing, mp3_channels), dtype=np.float32)
            chunk = np.vstack([chunk, silence])

    mp3_pos += frames

    outdata[:] = chunk
    analyze_audio(chunk)


load_mp3()

mic_stream = sd.InputStream(
    callback=mic_callback,
    channels=1,
    blocksize=2048
)
mic_stream.start()

mp3_stream = None

if mp3_data is not None:
    mp3_stream = sd.OutputStream(
        callback=mp3_callback,
        channels=mp3_channels,
        samplerate=mp3_sample_rate,
        blocksize=2048
    )
    mp3_stream.start()


vertex_shader_source = """
#version 330 core
layout (location = 0) in vec2 position;

void main() {
    gl_Position = vec4(position, 0.0, 1.0);
}
"""

fragment_shader_source = load_shader_file("shader.frag")


def compile_shader(source, shader_type):
    shader = glCreateShader(shader_type)
    glShaderSource(shader, source)
    glCompileShader(shader)

    if not glGetShaderiv(shader, GL_COMPILE_STATUS):
        error = glGetShaderInfoLog(shader).decode()
        raise Exception(error)

    return shader


vertex_shader = compile_shader(vertex_shader_source, GL_VERTEX_SHADER)
fragment_shader = compile_shader(fragment_shader_source, GL_FRAGMENT_SHADER)

shader_program = glCreateProgram()
glAttachShader(shader_program, vertex_shader)
glAttachShader(shader_program, fragment_shader)
glLinkProgram(shader_program)

if not glGetProgramiv(shader_program, GL_LINK_STATUS):
    error = glGetProgramInfoLog(shader_program).decode()
    raise Exception(error)


vertices = np.array([
    -1.0, -1.0,
     1.0, -1.0,
    -1.0,  1.0,
     1.0,  1.0
], dtype=np.float32)

vao = glGenVertexArrays(1)
vbo = glGenBuffers(1)

glBindVertexArray(vao)
glBindBuffer(GL_ARRAY_BUFFER, vbo)
glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, None)
glEnableVertexAttribArray(0)


u_resolution = glGetUniformLocation(shader_program, "u_resolution")
u_time = glGetUniformLocation(shader_program, "u_time")
u_mouse = glGetUniformLocation(shader_program, "u_mouse")
u_audio = glGetUniformLocation(shader_program, "u_audio")
u_bass = glGetUniformLocation(shader_program, "u_bass")
u_mid = glGetUniformLocation(shader_program, "u_mid")
u_treble = glGetUniformLocation(shader_program, "u_treble")
u_fft = glGetUniformLocation(shader_program, "u_fft")
u_theme = glGetUniformLocation(shader_program, "u_theme")
u_glow = glGetUniformLocation(shader_program, "u_glow")
u_particles = glGetUniformLocation(shader_program, "u_particles")
u_particle_life = glGetUniformLocation(shader_program, "u_particle_life")


running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

            if event.key == pygame.K_m:
                AUDIO_MODE = "mic" if AUDIO_MODE == "mp3" else "mp3"

            if event.key == pygame.K_p:
                mp3_playing = not mp3_playing

            if event.key == pygame.K_r:
                mp3_pos = 0

            if event.key == pygame.K_1:
                theme = 1

            if event.key == pygame.K_2:
                theme = 2

            if event.key == pygame.K_3:
                theme = 3

            if event.key == pygame.K_4:
                theme = 4

            if event.key == pygame.K_5:
                theme = 5

            if event.key == pygame.K_UP:
                glow_power = min(glow_power + 0.1, 2.0)

            if event.key == pygame.K_DOWN:
                glow_power = max(glow_power - 0.1, 0.4)

    mouse_x, mouse_y = pygame.mouse.get_pos()
    mouse_x = mouse_x / WIDTH
    mouse_y = 1.0 - (mouse_y / HEIGHT)

    current_time = time.time() - start_time

    smooth_audio = smooth_audio * 0.82 + raw_audio * 0.18
    smooth_bass = smooth_bass * 0.78 + bass * 0.22
    smooth_mid = smooth_mid * 0.82 + mid * 0.18
    smooth_treble = smooth_treble * 0.86 + treble * 0.14
    smooth_fft = smooth_fft * 0.75 + fft_levels * 0.25

    if current_time - last_spawn_time > 0.025:
        particles[particle_index] = {
            "x": mouse_x,
            "y": mouse_y,
            "life": 1.0
        }

        particle_index = (particle_index + 1) % MAX_PARTICLES
        last_spawn_time = current_time

    for particle in particles:
        particle["life"] = max(0.0, particle["life"] - 0.018)

    particle_positions = []
    particle_lives = []

    for particle in particles:
        particle_positions.extend([particle["x"], particle["y"]])
        particle_lives.append(particle["life"])

    particle_positions_np = np.array(particle_positions, dtype=np.float32)
    particle_lives_np = np.array(particle_lives, dtype=np.float32)

    glClear(GL_COLOR_BUFFER_BIT)
    glUseProgram(shader_program)

    glUniform2f(u_resolution, WIDTH, HEIGHT)
    glUniform1f(u_time, current_time)
    glUniform2f(u_mouse, mouse_x, mouse_y)
    glUniform1f(u_audio, smooth_audio)
    glUniform1f(u_bass, smooth_bass)
    glUniform1f(u_mid, smooth_mid)
    glUniform1f(u_treble, smooth_treble)
    glUniform1fv(u_fft, FFT_BANDS, smooth_fft)
    glUniform1i(u_theme, theme)
    glUniform1f(u_glow, glow_power)

    glUniform2fv(u_particles, MAX_PARTICLES, particle_positions_np)
    glUniform1fv(u_particle_life, MAX_PARTICLES, particle_lives_np)

    glBindVertexArray(vao)
    glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)

    pygame.display.flip()

    fps = int(clock.get_fps())

    pygame.display.set_caption(
        f"Visualizer | FPS:{fps} | Mode:{AUDIO_MODE} | "
        f"Audio:{smooth_audio:.2f} | Bass:{smooth_bass:.2f} | "
        f"Mid:{smooth_mid:.2f} | Treble:{smooth_treble:.2f}"
    )

    clock.tick(60)


mic_stream.stop()
mic_stream.close()

if mp3_stream:
    mp3_stream.stop()
    mp3_stream.close()

pygame.quit()