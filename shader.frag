#version 330 core
out vec4 FragColor;
uniform vec2 u_resolution;
uniform float u_time;
uniform vec2 u_mouse;
uniform float u_audio;
uniform int u_theme;
uniform float u_glow;
uniform int u_overlay;
uniform float u_bass;
uniform float u_mid;
uniform float u_treble;

uniform float u_fft[64];

uniform vec2 u_particles[32];
uniform float u_particle_life[32];

float ring(float d, float r, float t) {
    return smoothstep(t, 0.0, abs(d - r));
}

float glow(float d, float r, float strength) {
    return strength / max(abs(d - r), 0.006);
}

float hash(vec2 p) {
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
}

vec3 themeMain() {
    if (u_theme == 2) return vec3(0.95, 0.12, 1.0);
    if (u_theme == 3) return vec3(0.0, 1.0, 0.28);
    if (u_theme == 4) return vec3(0.35, 0.85, 1.0);
    if (u_theme == 5) return vec3(1.0, 0.08, 0.04);
    return vec3(1.0, 0.76, 0.48);
}

vec3 themeSoft() {
    if (u_theme == 2) return vec3(0.20, 0.75, 1.0);
    if (u_theme == 3) return vec3(0.45, 1.0, 0.55);
    if (u_theme == 4) return vec3(0.75, 0.95, 1.0);
    if (u_theme == 5) return vec3(1.0, 0.45, 0.12);
    return vec3(1.0, 0.88, 0.65);
}

vec3 themeGlow() {
    if (u_theme == 2) return vec3(0.55, 0.15, 1.0);
    if (u_theme == 3) return vec3(0.0, 0.85, 0.22);
    if (u_theme == 4) return vec3(0.20, 0.55, 1.0);
    if (u_theme == 5) return vec3(1.0, 0.18, 0.0);
    return vec3(1.0, 0.55, 0.22);
}

vec3 themeBackground() {
    if (u_theme == 2) return vec3(0.004, 0.002, 0.010);
    if (u_theme == 3) return vec3(0.001, 0.006, 0.002);
    if (u_theme == 4) return vec3(0.002, 0.006, 0.010);
    if (u_theme == 5) return vec3(0.010, 0.002, 0.001);
    return vec3(0.004, 0.003, 0.002);
}

void main() {
    vec2 uv = gl_FragCoord.xy / u_resolution.xy;
    vec2 p = uv - 0.5;
    p.x *= u_resolution.x / u_resolution.y;

    vec3 mainColor = themeMain();
    vec3 softColor = themeSoft();
    vec3 glowColor = themeGlow();

    vec3 color = themeBackground();
    if (u_overlay == 1) {
    color = vec3(0.0, 1.0, 0.0);
}

    // Beat flash background
    color += mainColor * u_audio * 0.035;

    // Bold stars
    vec2 starGrid = floor(uv * 55.0);
    vec2 starUV = fract(uv * 55.0) - 0.5;
    float starSeed = hash(starGrid);
    float starDist = length(starUV);
    float starMask = step(0.955, starSeed);

    float starCore = smoothstep(0.070, 0.0, starDist) * starMask;
    float starGlow = 0.010 / max(starDist, 0.018) * starMask;

    float cross =
    (
        smoothstep(0.035, 0.0, abs(starUV.x)) *
        smoothstep(0.22, 0.0, abs(starUV.y)) +
        smoothstep(0.035, 0.0, abs(starUV.y)) *
        smoothstep(0.22, 0.0, abs(starUV.x))
    ) * starMask;

    float twinkle = sin(u_time * (3.0 + starSeed * 7.0) + starSeed * 30.0) * 0.5 + 0.5;

    color += vec3(1.0, 0.92, 0.72) * starCore * (1.4 + twinkle * 1.5);
    color += vec3(1.0, 0.75, 0.35) * starGlow * (0.25 + twinkle * 0.25);
    color += vec3(1.0, 0.95, 0.80) * cross * (0.45 + twinkle * 0.65);

    // Shooting stars
    for (int i = 0; i < 3; i++) {
        float fi = float(i);
        float t = fract(u_time * 0.12 + fi * 0.33);

        vec2 start = vec2(-0.8 + fi * 0.55, 0.45 - fi * 0.18);
        vec2 dir = normalize(vec2(1.0, -0.35));
        vec2 meteorPos = start + dir * t * 2.2;

        float meteorDist = length(p - meteorPos);
        float meteorCore = smoothstep(0.020, 0.0, meteorDist);

        float trail = smoothstep(0.35, 0.0, length(p - (meteorPos - dir * 0.20)));
        float line = smoothstep(0.020, 0.0, abs(dot(p - meteorPos, vec2(-dir.y, dir.x)))) *
                     smoothstep(0.35, 0.0, dot(meteorPos - p, dir));

        color += vec3(1.0, 0.85, 0.55) * meteorCore * 1.4;
        color += softColor * line * trail * 0.45;
    }

    vec2 mouseCenter = u_mouse - 0.5;
    mouseCenter.x *= u_resolution.x / u_resolution.y;

    vec2 c1 = mouseCenter + vec2(0.08, -0.02);
    vec2 c2 = mouseCenter + vec2(
        -0.18 + sin(u_time * 0.75) * 0.12,
         0.02 + cos(u_time * 0.65) * 0.06
    );

    float d1 = length(p - c1);
    float d2 = length(p - c2);

    float r1 = 0.34 + u_audio * 0.025;
    float r2 = 0.23 + sin(u_time * 1.2) * 0.025 + u_audio * 0.040;

    float mainRing = ring(d1, r1, 0.010);
    float smallRing = ring(d2, r2, 0.008);

    color += mainColor * mainRing * 2.0;
    color += softColor * smallRing * 1.7;

    color += glowColor * glow(d1, r1, 0.024 * u_glow);
    color += glowColor * glow(d2, r2, 0.019 * u_glow);

    float intersection = mainRing * smallRing;
    color += vec3(1.0, 0.96, 0.80) * intersection * 4.5;

    // Orbiting mini dots
    for (int i = 0; i < 12; i++) {
        float fi = float(i);
        float angle = fi * 0.5236 + u_time * 0.9;
        float orbitRadius = 0.39 + sin(u_time * 1.5 + fi) * 0.015 + u_audio * 0.025;

        vec2 dotPos = c1 + vec2(cos(angle), sin(angle)) * orbitRadius;
        float od = length(p - dotPos);

        float dotCore = smoothstep(0.020, 0.0, od);
        float dotGlow = 0.010 / max(od, 0.010);

        float pulse = sin(u_time * 3.0 + fi * 1.7) * 0.5 + 0.5;

        color += softColor * dotCore * (1.1 + pulse + u_audio * 1.5);
        color += glowColor * dotGlow * 0.07 * u_glow;
    }

    // Circular Audio Spectrum
    vec2 q = p - c1;
    float angle = atan(q.y, q.x);
    float angleNorm = (angle + 3.14159) / 6.28318;

    float bands = 96.0;
    float bandIndex = floor(angleNorm * bands);

    float audioWave = sin(bandIndex * 0.45 + u_time * 4.0) * 0.5 + 0.5;

   
    float spikeBase = 0.42;
    float radial = length(q);
    float spokeWidth =
    smoothstep(
        0.008,
        0.0,
        abs(fract(angleNorm * bands) - 0.5)
    );
   float spikeHeight = 0.020 + audioWave * 0.018 + u_mid * (0.040 + audioWave * 0.040);

    float spike =
        spokeWidth *
        step(spikeBase, radial) *
        step(radial, spikeBase + spikeHeight);

    color += softColor * spike * (0.8 + u_audio * 2.0);
    color += glowColor * spike * 0.55 * u_glow;

    // Infinite ripple rings
    for (int i = 0; i < 7; i++) {
        float fi = float(i);
        float rippleRadius = fract(u_time * 0.18 + fi * 0.16) * 0.75;

        float fade = 1.0 - rippleRadius / 0.75;
        fade = fade * fade;

        float ripple = ring(d1, rippleRadius, 0.006 + u_audio * 0.004);

        color += mainColor * ripple * fade * (0.25 + u_audio * 1.3);
        color += glowColor * glow(d1, rippleRadius, 0.004 * u_glow) * fade * (0.35 + u_audio);
    }

    // Particle trail
    for (int i = 0; i < 32; i++) {
        vec2 pp = u_particles[i] - 0.5;
        pp.x *= u_resolution.x / u_resolution.y;

        float life = u_particle_life[i];
        float pd = length(p - pp);

        float particleCore = smoothstep(0.030, 0.0, pd);
        float particleGlow = 0.012 / max(pd, 0.008);

        color += softColor * particleCore * life * (1.2 + u_audio * 2.0);
        color += glowColor * particleGlow * life * 0.08 * u_glow;
    }

    // Bloom
    float brightness = max(color.r, max(color.g, color.b));
    color += color * smoothstep(0.45, 1.2, brightness) * 0.45 * u_glow;

    // Glass audio panel
    vec2 boxMin = vec2(0.035, 0.62);
    vec2 boxMax = vec2(0.43, 0.89);

    float insideBox =
        step(boxMin.x, uv.x) * step(uv.x, boxMax.x) *
        step(boxMin.y, uv.y) * step(uv.y, boxMax.y);

    float edge =
        step(uv.x, boxMin.x + 0.003) +
        step(boxMax.x - 0.003, uv.x) +
        step(uv.y, boxMin.y + 0.003) +
        step(boxMax.y - 0.003, uv.y);

    float border = insideBox * edge;

    vec3 glassColor = themeBackground() * 4.0 + softColor * 0.035;
    color = mix(color, glassColor, insideBox * 0.58);
    color += softColor * border * 0.55;

    // Audio bars
    // Live FFT Frequency Bars
float bars = 64.0;
float localX = (uv.x - boxMin.x) / (boxMax.x - boxMin.x);
float localY = (uv.y - boxMin.y) / (boxMax.y - boxMin.y);

float index = floor(localX * bars);
float bx = fract(localX * bars);

int fftIndex = int(clamp(index, 0.0, 63.0));
float band = u_fft[fftIndex];

float barHeight = 0.06 + band * 0.86;
barHeight = clamp(barHeight, 0.05, 0.95);

float barWidth = step(0.18, bx) * step(bx, 0.78);

float body =
    insideBox *
    barWidth *
    step(localY, barHeight) *
    step(0.04, localY);

float cap =
    insideBox *
    barWidth *
    smoothstep(0.025, 0.0, abs(localY - barHeight)) *
    step(0.04, localY);

vec3 freqColor = mix(mainColor, softColor, index / bars);

color += freqColor * body * (0.6 + band * 2.0);
color += vec3(1.0, 0.95, 0.75) * cap * (1.2 + band * 2.5);
color += freqColor *
    smoothstep(0.08, 0.0, abs(localY - barHeight)) *
    barWidth *
    insideBox *
    0.25;
    

    float vig = smoothstep(0.90, 0.18, length(uv - 0.5));
    color *= vig;

    FragColor = vec4(color, 1.0);
}