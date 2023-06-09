import os
import shutil
from mutagen.easyid3 import EasyID3

def organize_mp3_files(root_folder):
    # Iterate through all files and directories recursively
    for root, dirs, files in os.walk(root_folder):
        for file_name in files:
            if file_name.endswith(".mp3"):
                mp3_file_path = os.path.join(root, file_name)
                try:
                    # Extract metadata tags from MP3 file
                    mp3 = EasyID3(mp3_file_path)
                    artist = mp3["artist"][0]
                    album = mp3["album"][0]
                    title = mp3["title"][0]
                    track_number = mp3["tracknumber"][0].split('/')[0]
                    
                    # Create destination directory in the format "artist/album"
                    destination_folder = os.path.join(artist, album)
                    os.makedirs(destination_folder, exist_ok=True)
                    
                    # Rename and move the MP3 file to the destination directory
                    new_file_name = f"{track_number} {title}.mp3"
                    new_file_path = os.path.join(destination_folder, new_file_name)
                    shutil.move(mp3_file_path, new_file_path)
                    
                    print(f"Moved: {mp3_file_path} -> {new_file_path}")
                except Exception as e:
                    print(f"Failed to process file: {mp3_file_path}")
                    print(f"Error: {str(e)}")

# Specify the root folder where the MP3 files are located
root_folder = "."

# Call the function to organize the MP3 files
organize_mp3_files(root_folder)
