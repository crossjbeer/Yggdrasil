import argparse
import os
import subprocess
from pathlib import Path 


def locate_mkv_files(directory):
    """
    Locates MKV files in the specified directory.

    Args:
        directory (str): The directory to search for MKV files.

    Returns:
        list: A list of MKV file paths.

    """

    try:
        mkv_files = [file for file in os.listdir(directory) if file.endswith(".mkv")]
    except OSError as e:
        print(f"Error occurred while locating MKV files in {directory}: {e}")
        mkv_files = []
    return mkv_files


def sort_files(files):
    return sorted(files)

def rename_files(files, path):
    """
    Renames files in the given path.

    Args:
        files (list): The list of files to be renamed.
        path (str): The path where the files are located.

    Returns:
        list: A list of new file paths after renaming.

    """
    newname = []
    for i, file in enumerate(files):
        new_name = f"{i+1}.mkv"
        new_path = os.path.join(path, new_name)
        try:
            os.rename(file, new_path)
            newname.append(new_path)
        except OSError as e:
            print(f"Error occurred while renaming {file}: {e}")
    return newname

def convert_to_wav(file):
    """
    Converts the given MKV file to WAV format. This uses the 'ffmpeg' package. 
    The file is converted to a 16kHz, Mono wav file. This is the standard format for all downstream purposes. 

    Args:
        file (str): The path of the MKV file to be converted.

    """
    output_file = os.path.splitext(file)[0] + ".wav"
    try:
        subprocess.call(["ffmpeg", "-i", file, "-ac", "1", "-ar", "16000", output_file])
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while converting {file} to WAV: {e}")

def combine_wav_files(files, save_path):
    """
    Combines multiple WAV files into a single WAV file.
    Assumes files arrive sorted. 

    Args:
        files (list): The list of WAV files to be combined.
        save_path (str): The path where the combined WAV file should be saved.

    """
    output_file = os.path.join(save_path)
    command = ["sox"]
    command.extend(files)
    command.append(output_file)
    try:
        subprocess.call(command)
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while combining WAV files: {e}")

def delete_wav_files(wav_files):
    for file in wav_files:
        os.remove(file)

def main(path, savepath, savename):
    """
    Main function to execute the MKV to WAV conversion and combining process.

    Args:
        directory (str): The directory containing MKV files.
        save_path (str): The path to save the combined WAV file.

    """
        
    mkv_files = locate_mkv_files(path)
    if not mkv_files:
        print("No MKV files found.")
        return
    
    if(not savename):
        p = Path(path)
        pparts = p.parts 
        savename = pparts[-1]

    sorted_files = sort_files(mkv_files)
    sorted_files_full_path = [os.path.join(path, i) for i in sorted_files]

    if not sorted_files_full_path:
        print("No files renamed. Exiting.")
        return

    wav_files = []
    for file in sorted_files_full_path:
        convert_to_wav(file)

        wav_file = os.path.splitext(file)[0] + ".wav"
        if os.path.isfile(wav_file):
            wav_files.append(wav_file)
        else:
            print(f"Conversion failed for file: {file}")

    if not wav_files:
        print("No WAV files generated. Exiting.")
        return

    combine_wav_files(wav_files, os.path.join(savepath, savename + '.wav'))

    delete_wav_files(wav_files)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Data ingestion pipeline")
    parser.add_argument('-p', "--path", required=True, help="Directory containing .mkv files", type=str)
    parser.add_argument('-sp', "--savepath", required=True, help="Path to save the combined .wav file", type=str)
    parser.add_argument('-sn', '--savename', help='Name for combined audio .wav', required=False, type=str, default=None)
    args = parser.parse_args()

    main(args.path, args.savepath, args.savename)