import os


# Define the folder where the .ogg files are stored
sounds_folder = "sounds"

# Get the list of all .ogg files in the sounds folder
ogg_files = [f for f in os.listdir(sounds_folder) if f.endswith(".ogg")]

file_name = "description.ext"


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
            # Read first page to verify OGG signature and get page size
            if f.read(4) != b'OggS':
                raise ValueError("Not a valid OGG file")
            
            # Reset to start and read first few KB to find headers
            f.seek(0)
            header_data = f.read(8192)
            
            # Find start of Vorbis identification header
            vorbis_header_pos = -1
            for i in range(len(header_data) - 7):
                # Look for Vorbis identification header pattern
                if (header_data[i] == 1 and    # header packet type
                    header_data[i+1:i+7] == b'vorbis'):  # vorbis signature
                    vorbis_header_pos = i
                    break
            
            if vorbis_header_pos == -1:
                raise ValueError("Could not find Vorbis identification header")
            
            # Parse Vorbis identification header
            pos = vorbis_header_pos + 7  # Skip packet type and 'vorbis'
            version = int.from_bytes(header_data[pos:pos+4], 'little')
            if version != 0:
                raise ValueError(f"Unsupported Vorbis version: {version}")
                
            channels = header_data[pos+4]
            sample_rate = int.from_bytes(header_data[pos+5:pos+9], 'little')
            
            if not (8000 <= sample_rate <= 192000):  # Sanity check
                raise ValueError(f"Invalid sample rate: {sample_rate}")
            
            log(f"Channels: {channels}")
            log(f"Sample rate: {sample_rate} Hz")
            
            # Get file size
            f.seek(0, 2)
            file_size = f.tell()
            log(f"File size: {file_size} bytes")
            
            # Find last page
            search_size = min(file_size, 65536)
            f.seek(-search_size, 2)
            data = f.read(search_size)
            
            last_oggs_pos = data.rindex(b'OggS')
            f.seek(-search_size + last_oggs_pos, 2)
            
            # Get granule position from last page
            f.seek(6, 1)  # Skip to granule position
            granule = int.from_bytes(f.read(8), 'little')
            log(f"Final granule position: {granule}")
            
            # Calculate duration
            duration = granule / sample_rate
            log(f"Calculated duration: {duration:.2f} seconds")
            
            return duration
            
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except Exception as e:
        raise ValueError(f"Error reading OGG file: {str(e)}")


# Open the file in write mode. If it doesn't exist, it will be created
with open(file_name, "w") as file:
    file.write("class CfgSounds\n")
    file.write("{\n")
    file.write("    tracks[]={};\n")
    
    # Create a class for each .ogg file
    for ogg_file in ogg_files:
        # Remove the file extension and replace spaces with underscores
        track_name = os.path.splitext(ogg_file)[0].replace(" ", "_")
        ogg_file_path = os.path.join(sounds_folder, ogg_file)  # Full path to .ogg file
        
        # Calculate the duration of the ogg file
        try:
            duration = calculate_duration(ogg_file_path, debug=False)  # Disabled debug output
        except ValueError as e:
            print(f"Skipping file {ogg_file} due to error: {e}")
            continue
        
        file.write(f"\n")
        file.write(f"    class {track_name}\n")
        file.write(f"    {{\n")
        file.write(f"        name = \"{track_name}\";\n")
        file.write(f"        sound[] = {{\"\\{sounds_folder}\\{ogg_file}\", {duration}, 1.0}};\n")
        file.write(f"        titles[] = {{}};\n")
        file.write(f"    }};\n")
    
    file.write("};\n")

print(f"File '{file_name}' has been created successfully.")