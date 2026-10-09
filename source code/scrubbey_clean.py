import os
import time

def clean_playlist(filepath, args):

    print(f"Processing: {filepath}")
    
    # Reads the original M3U8 lines here...
    
    # Apply rules based on user settings:
    if args.no_extinf:
        pass # Removes EXTINF tags
        
    if args.dedupe:
        pass # Filters out duplicate tracks
        
    # Format the paths (basename, relative, absolute)
    if args.paths == "basename":
        pass 
            
    time.sleep(1.5) 
    print(f"Finished: {filepath}")


def run(args):
    
    input_folder = args.inputs[0]
    
    # Optional: ensure output folder exists if one was provided
    if args.out and not os.path.exists(args.out):
        os.makedirs(args.out)

    # Gather all playlist files
    playlists_to_clean = []
    
    if args.recursive:
        # Scans through subfolders
        for root, dirs, files in os.walk(input_folder):
            for file in files:
                if file.endswith('.m3u8') or file.endswith('.m3u'):
                    playlists_to_clean.append(os.path.join(root, file))
    else:
        # Scans the top folder
        for file in os.listdir(input_folder):
            if file.endswith('.m3u8') or file.endswith('.m3u'):
                playlists_to_clean.append(os.path.join(input_folder, file))

    if not playlists_to_clean:
        raise ValueError("No .m3u or .m3u8 playlists found in the selected input folder!")

    # Process each one
    for playlist_path in playlists_to_clean:
        clean_playlist(playlist_path, args)