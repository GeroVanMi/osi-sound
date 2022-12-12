import wave
import math
import sys
import json

printdebug = lambda s: None

if len(sys.argv) < 2:
    exit("Syntax: notes-from-sine-waves <wavfile>")

# Get the first argument
wavfile_path = sys.argv[1]

# Open the wave file
wave_file = wave.open(wavfile_path)


# TODO: What are channels?
channels = wave_file.getnchannels()  # 1
# Bit depth of the audio (in bytes)
re = wave_file.getsampwidth()  # 2

# TODO: This might be clear once we understand re
#   Bytes multiplied by channels (But why?)
width = (re * channels)

# spectrum is equal to 2 to the power of (8*re)
# We multiply by 8 because it is in bytes, and we want in bits
spectrum = 2 ** (re * 8)
zlinepre = spectrum // 2

s = wave_file.getnframes() / wave_file.getframerate()
print(f"Audio duration: {wave_file.getnframes()} frames with {s} seconds")
print(f"Audio format: {wave_file.getframerate()} Hz, {re * 8} bit, {channels} channels")

# mindiff = 1000
# mindist = 20

blocksize = 2 ** 20
s = wave_file.readframes(blocksize)
# "//" is division and rounding down
frames = len(s) // width
print(f"Audio reading: {blocksize:7} requested frames = {len(s):8} received bytes = {frames:7} received frames")

last_value = 0
last_zero_pos = 0
last_note = None
last_note_pos = 0
notes_list = []

for frame_index in range(frames):
    vec = s[frame_index * width:(frame_index + 1) * width]
    if channels > 1:
        # use right channel, seems to be default on Linux audio capture but does not matter for synthesised files
        vec = vec[re:]
    value = vec[0]
    if re == 2:
        # combine two 8-bit amplitude values into one 16-bit amplitude
        value = vec[1] * 256 + vec[0]
    if value > zlinepre:
        # signed representation (curve around x-axis) while wave module gives only unsigned
        value -= spectrum

    printdebug(f"READ: pos={frame_index:6} val={value:5}")

    change = False
    if value >= 0 and last_value < 0:
        change = True
    last_value = value

    if change:
        distance = frame_index - last_zero_pos
        freq = 1 / (distance / wave_file.getframerate())
        pitch = int(freq)
        pitch = (math.log(int(freq), 2) - math.log(440, 2)) * 12 + 9

        printdebug(f"WAVE: wavelen={distance:4} freq=~{int(freq):4} Hz")
        last_zero_pos = frame_index

        if abs(pitch - round(pitch)) < 0.2:
            rpitch = int(round(pitch))
            keytable = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "H"]
            note = keytable[rpitch % 12]
            octave = rpitch // 12
            if octave > 0:
                note += "+"
            elif octave < 0:
                note += "-"
            normfreq = round(440 * 2 ** ((rpitch - 9) / 12), 1)
            printdebug(f"NOTE partial: note=~{note:3} {normfreq:4} Hz @ {frame_index:7}")
        else:
            note = None

        if note != last_note:
            if last_note is not None:
                # FIXME: the factor 2 is not quite clear...
                seconds = 2 * (frame_index - last_note_pos) / wave_file.getframerate()
                # skip very short notes that are likely inaccuracies related to frequency changes
                if seconds > 0.1:
                    # quantify to ½ seconds resolution - small rounding errors are expected to result from chunked input data
                    roundedseconds = int(round(seconds * 2)) / 2
                    if roundedseconds < 0.5:
                        # FIXME: workaround for high pitches that appear shorter, not quite clear why
                        roundedseconds = 0.5
                    print(
                        f"NOTE complete: {last_note:3} [{last_note_pos:7}..{frame_index - 1:7}] = ~ {roundedseconds} s ({round(seconds, 2)}  s)")
                    notes_list.append((last_note, roundedseconds))
            last_note = note
            last_note_pos = frame_index

if notes_list:
    f = open(wavfile_path + ".json", "w")
    json.dump(notes_list, f)
    f.close()
    print(f"Notes reproduced in {wavfile_path}.json.")
else:
    print("No notes found.")
