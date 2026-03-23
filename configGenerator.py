import os
import re

# Always resolve paths relative to the script's own location
script_dir = os.path.dirname(os.path.abspath(__file__))
sounds_folder = os.path.join(script_dir, "sounds")
file_name = os.path.join(script_dir, "description.ext")

if not os.path.isdir(sounds_folder):
    print(f"ERROR: sounds folder not found at:\n  {sounds_folder}")
    input("Press Enter to exit...")
    exit(1)

ogg_files = [f for f in os.listdir(sounds_folder) if f.endswith(".ogg")]

if not ogg_files:
    print("WARNING: No .ogg files found in the sounds folder.")
    input("Press Enter to exit...")
    exit(1)


def calculate_duration(file_path, debug=False):
    """
    Get the duration of an OGG file in seconds without using external libraries.

    Args:
        file_path (str): Path to the OGG file
        debug (bool): If True, print debug information

    Returns:
        float: Duration of the file in seconds
    """
    def log(msg):
        if debug:
            print(msg)

    try:
        with open(file_path, 'rb') as f:
            if f.read(4) != b'OggS':
                raise ValueError("Not a valid OGG file")

            f.seek(0)
            header_data = f.read(8192)

            vorbis_header_pos = -1
            for i in range(len(header_data) - 7):
                if (header_data[i] == 1 and
                        header_data[i+1:i+7] == b'vorbis'):
                    vorbis_header_pos = i
                    break

            if vorbis_header_pos == -1:
                raise ValueError("Could not find Vorbis identification header")

            pos = vorbis_header_pos + 7
            version = int.from_bytes(header_data[pos:pos+4], 'little')
            if version != 0:
                raise ValueError(f"Unsupported Vorbis version: {version}")

            channels = header_data[pos+4]
            sample_rate = int.from_bytes(header_data[pos+5:pos+9], 'little')

            if not (8000 <= sample_rate <= 192000):
                raise ValueError(f"Invalid sample rate: {sample_rate}")

            log(f"Channels: {channels}")
            log(f"Sample rate: {sample_rate} Hz")

            f.seek(0, 2)
            file_size = f.tell()
            log(f"File size: {file_size} bytes")

            search_size = min(file_size, 65536)
            f.seek(-search_size, 2)
            data = f.read(search_size)

            last_oggs_pos = data.rindex(b'OggS')
            f.seek(-search_size + last_oggs_pos, 2)

            f.seek(6, 1)
            granule = int.from_bytes(f.read(8), 'little')
            log(f"Final granule position: {granule}")

            duration = granule / sample_rate
            log(f"Calculated duration: {duration:.2f} seconds")

            return duration

    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except Exception as e:
        raise ValueError(f"Error reading OGG file: {str(e)}")


def build_cfg_sounds_block():
    """Build the CfgSounds class block as a string."""
    lines = []
    lines.append("class CfgSounds\n")
    lines.append("{\n")
    lines.append("    tracks[]={};\n")

    for ogg_file in ogg_files:
        track_name = os.path.splitext(ogg_file)[0].replace(" ", "_")
        ogg_file_path = os.path.join(sounds_folder, ogg_file)

        try:
            duration = calculate_duration(ogg_file_path, debug=False)
        except ValueError as e:
            print(f"Skipping file {ogg_file} due to error: {e}")
            continue

        lines.append(f"\n")
        lines.append(f"    class {track_name}\n")
        lines.append(f"    {{\n")
        lines.append(f"        name = \"{track_name}\";\n")
        lines.append(f"        sound[] = {{\"\\sounds\\{ogg_file}\", {duration}, 1.0}};\n")
        lines.append(f"        titles[] = {{}};\n")
        lines.append(f"    }};\n")

    lines.append("};\n")
    return "".join(lines)


# Read existing file content if it exists
if os.path.exists(file_name):
    with open(file_name, "r") as f:
        existing_content = f.read()
else:
    existing_content = ""

new_block = build_cfg_sounds_block()

# Replace existing CfgSounds block if present, otherwise append
cfg_sounds_pattern = re.compile(
    r'class\s+CfgSounds\s*\{.*?\};',
    re.DOTALL | re.IGNORECASE
)

if cfg_sounds_pattern.search(existing_content):
    new_content = cfg_sounds_pattern.sub(new_block.rstrip("\n"), existing_content)
    print("Replaced existing CfgSounds block.")
else:
    separator = "\n" if existing_content and not existing_content.endswith("\n") else ""
    new_content = existing_content + separator + new_block
    print("No existing CfgSounds block found — appended new block.")

with open(file_name, "w") as f:
    f.write(new_content)

print(f"File '{file_name}' has been updated successfully.")
input("Press Enter to exit...")