"""Petits sons synthétiques, sans fichiers audio externes.

Le navigateur peut refuser l'audio avant la première interaction. La banque
reste donc silencieuse si l'initialisation échoue, puis réessaie au prochain
clic/tir.
"""

import io
import math
import random
import struct
import sys

import pygame


SAMPLE_RATE = 22050


def _wav_bytes(samples):
    pcm = bytearray()
    for sample in samples:
        value = max(-1.0, min(1.0, sample))
        pcm.extend(struct.pack("<h", int(value * 32767)))

    data_size = len(pcm)
    header = (
        b"RIFF"
        + struct.pack("<I", 36 + data_size)
        + b"WAVEfmt "
        + struct.pack(
            "<IHHIIHH",
            16,
            1,
            1,
            SAMPLE_RATE,
            SAMPLE_RATE * 2,
            2,
            16,
        )
        + b"data"
        + struct.pack("<I", data_size)
    )
    return header + pcm


def _tone(duration, start_hz, end_hz=None, volume=0.35):
    count = max(1, int(duration * SAMPLE_RATE))
    end_hz = start_hz if end_hz is None else end_hz
    phase = 0.0
    samples = []
    for i in range(count):
        t = i / max(1, count - 1)
        hz = start_hz + (end_hz - start_hz) * t
        phase += math.tau * hz / SAMPLE_RATE
        envelope = (1.0 - t) ** 1.8
        samples.append(math.sin(phase) * envelope * volume)
    return samples


def _noise(duration, volume=0.45, seed=0, low_tone=0.0):
    rng = random.Random(seed)
    count = max(1, int(duration * SAMPLE_RATE))
    samples = []
    smoothed = 0.0
    phase = 0.0
    for i in range(count):
        t = i / max(1, count - 1)
        smoothed = smoothed * 0.72 + rng.uniform(-1.0, 1.0) * 0.28
        phase += math.tau * 58.0 / SAMPLE_RATE
        envelope = (1.0 - t) ** 2.2
        samples.append((smoothed + math.sin(phase) * low_tone) * envelope * volume)
    return samples


def _sequence(notes, note_duration=0.09, volume=0.28):
    samples = []
    for hz in notes:
        samples.extend(_tone(note_duration, hz, hz * 1.02, volume))
    return samples


class SoundBank:
    def __init__(self):
        self.muted = False
        self.ready = False
        self.sounds = {}
        self._web_eval = None
        self.is_web = sys.platform in ("emscripten", "wasm")
        try:
            import platform

            if hasattr(platform, "window"):
                self.is_web = True
                self._web_eval = platform.window.eval
        except Exception:
            pass
        self.web_ready = self._install_web_audio() if self.is_web else False

    def _install_web_audio(self):
        if self._web_eval is None:
            return False
        code = r"""
(() => {
  if (window.GorillaAudio) return true;

  let context = null;
  const AudioContext = window.AudioContext || window.webkitAudioContext;
  if (!AudioContext) return false;

  const getContext = () => {
    if (!context) context = new AudioContext();
    return context;
  };

  const unlock = () => {
    try {
      const audio = getContext();
      if (audio.state === "suspended") audio.resume();
    } catch (_) {}
  };
  window.addEventListener("pointerdown", unlock, { capture: true });
  window.addEventListener("keydown", unlock, { capture: true });

  const tone = (audio, when, duration, from, to, volume, type = "square") => {
    const oscillator = audio.createOscillator();
    const gain = audio.createGain();
    oscillator.type = type;
    oscillator.frequency.setValueAtTime(from, when);
    oscillator.frequency.exponentialRampToValueAtTime(Math.max(20, to), when + duration);
    gain.gain.setValueAtTime(volume, when);
    gain.gain.exponentialRampToValueAtTime(0.0001, when + duration);
    oscillator.connect(gain).connect(audio.destination);
    oscillator.start(when);
    oscillator.stop(when + duration);
  };

  const noise = (audio, when, duration, volume) => {
    const length = Math.max(1, Math.floor(audio.sampleRate * duration));
    const buffer = audio.createBuffer(1, length, audio.sampleRate);
    const data = buffer.getChannelData(0);
    for (let i = 0; i < length; i++) {
      data[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / length, 2);
    }
    const source = audio.createBufferSource();
    const gain = audio.createGain();
    source.buffer = buffer;
    gain.gain.setValueAtTime(volume, when);
    gain.gain.exponentialRampToValueAtTime(0.0001, when + duration);
    source.connect(gain).connect(audio.destination);
    source.start(when);
  };

  const play = (name) => {
    try {
      const audio = getContext();
      if (audio.state === "suspended") audio.resume();
      const now = audio.currentTime;
      if (name === "click") tone(audio, now, .055, 520, 760, .055);
      else if (name === "throw") tone(audio, now, .19, 240, 920, .075, "sawtooth");
      else if (name === "impact") noise(audio, now, .10, .13);
      else if (name === "explosion") {
        noise(audio, now, .38, .22);
        tone(audio, now, .32, 90, 38, .11, "sawtooth");
      } else if (name === "thunder") {
        noise(audio, now, .72, .16);
        tone(audio, now, .58, 72, 28, .08, "sawtooth");
      } else {
        const notes = name === "victory"
          ? [392, 523.25, 659.25, 783.99, 1046.5]
          : [523.25, 659.25, 783.99];
        const step = name === "victory" ? .105 : .085;
        notes.forEach((hz, index) => {
          tone(audio, now + index * step, step * .9, hz, hz * 1.02, .055);
        });
      }
    } catch (_) {}
  };

  window.GorillaAudio = { play };
  return true;
})()
"""
        try:
            return bool(self._web_eval(code))
        except Exception:
            return False

    def ensure_ready(self):
        if self.ready:
            return True
        if self.is_web:
            # Le mixeur SDL peut bloquer la boucle Pygbag. Web Audio reste
            # non bloquant ; si indisponible, le jeu continue en silence.
            self.ready = True
            return self.web_ready
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(
                    frequency=SAMPLE_RATE,
                    size=-16,
                    channels=1,
                    buffer=512,
                )
            definitions = {
                "click": _tone(0.055, 520, 760, 0.22),
                "throw": _tone(0.19, 240, 920, 0.28),
                "impact": _noise(0.10, 0.28, seed=7),
                "explosion": _noise(0.38, 0.62, seed=19, low_tone=0.9),
                "thunder": _noise(0.72, 0.42, seed=29, low_tone=0.65),
                "score": _sequence((523.25, 659.25, 783.99), 0.085, 0.24),
                "victory": _sequence(
                    (392.00, 523.25, 659.25, 783.99, 1046.50),
                    0.105,
                    0.28,
                ),
            }
            self.sounds = {
                name: pygame.mixer.Sound(file=io.BytesIO(_wav_bytes(samples)))
                for name, samples in definitions.items()
            }
            self.ready = True
        except (pygame.error, OSError, ValueError):
            self.ready = False
        return self.ready

    def play(self, name):
        if self.muted:
            return
        if self.is_web:
            if self.ensure_ready() and name in {
                "click",
                "throw",
                "impact",
                "explosion",
                "thunder",
                "score",
                "victory",
            }:
                try:
                    self._web_eval("window.GorillaAudio.play('%s')" % name)
                except Exception:
                    pass
            return
        if not self.ensure_ready():
            return
        sound = self.sounds.get(name)
        if sound is not None:
            try:
                sound.play()
            except pygame.error:
                pass

    def toggle(self):
        self.muted = not self.muted
        if not self.is_web and self.muted and pygame.mixer.get_init():
            pygame.mixer.stop()
        else:
            self.play("click")
        return self.muted
