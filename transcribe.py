import whisper as wisp 
import argparse 
import os 
import json 
import soundfile as sf 
import pandas as pd 
from pathlib import Path


def transcribe_wav(wav, model):
    """
    Transcribes the audio file using the Whisper model and returns the transcription result as a dictionary.

    Args:
        wav (str): Path to the .wav file.
        model (str): Whisper model to use [tiny.en, small.en, base.en, medium.en, large.en].

    Returns:
        dict: Transcription result dictionary.
    """

    try:
        model = wisp.load_model(model)
        audio = wisp.load_audio(wav)
    except Exception as e:
        raise ValueError("Failed to load model or audio file.") from e

    try:
        result_dict = wisp.transcribe(model, audio)
    except Exception as e:
        raise ValueError("Transcription failed.") from e

    return result_dict


def save_transcription_as_json(res_dict, path):
    segs = res_dict['segments']

    path = os.path.join(path, 'res.json')

    with open(path, 'w') as of:
        json.dump(segs, of)

def segment_to_dataframe(segments):
    """
    Converts the segments from the transcription result dictionary into a pandas DataFrame.

    Args:
        segments (list): List of segment dictionaries.

    Returns:
        pandas.DataFrame: DataFrame containing the segments.
    """

    allSegments = pd.DataFrame()
    for i, segment in enumerate(segments):
        segment['tokens'] = [segment['tokens']]

        segment = pd.DataFrame(index=[i]).from_dict(segment, orient='columns')

        allSegments = pd.concat([allSegments, segment], axis=0)

    return(allSegments)

def segment_audio(segDF, wav, savepath, lead=0, tail=0):
    """
    Segments the audio file based on the start and end times provided in the DataFrame.

    Args:
        segDF (pandas.DataFrame): DataFrame containing the segment information.
        wav (str): Path to the input .wav file.
        savepath (str): Path to save the segmented .wav files.
        lead (float): Lead time (in seconds) to include before the start time.
        tail (float): Tail time (in seconds) to include after the end time.
    """

    try:
        os.mkdir(savepath := os.path.join(savepath, 'segments'))
    except:
        print("Unable to build segment save dir. Defaulting to original savepath...")
        savepath = savepath

    startStop = segDF[['start', 'end']]
    startStop = startStop.values
    startStop = [(i[0], i[1]) for i in startStop]

    try:
        data, sample_rate = sf.read(wav)
    except Exception as e:
        raise ValueError("Failed to read the input WAV file.") from e

    for i, (start, end) in enumerate(startStop):
        start_samp = int(start * sample_rate)
        end_samp = int(end * sample_rate)

        output_file = os.path.join(savepath, f'split_{i+1}.wav')
        try:
            sf.write(output_file, data[start_samp:end_samp], sample_rate)
        except Exception as e:
            raise ValueError(f"Failed to save segment {i+1} as a WAV file.") from e


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Whisper ASR Transcription')
    parser.add_argument('-p', '--path', help='Path to the .wav file', required=True)
    parser.add_argument('-m', '--model', help='Whisper Model to Use [tiny.en, small.en, base.en, medium.en, large.en]', default='base')
    parser.add_argument('-sp', '--savepath', help='Path to save .json', default=None)
    parser.add_argument('-sn', '--savename', help='Name to save transcription .csv under', required=False, type=str)
    parser.add_argument('--segment', help='option to segment provided .wav file and save to savepath', action='store_true')
    args = parser.parse_args()

    # Check if the provided path exists
    if(not os.path.exists(args.path)):
        raise ValueError("Input file path does not exist.")

    # Check if the save path exists, and if not, attempt to create it
    if(args.savepath):
        if(not os.path.exists(args.savepath)):
            try:
                print("Building save dir...")
                os.makedirs(args.savepath)
            except Exception as e:
                raise ValueError("Failed to create the save directory.") from e

        # Determine the savename based on the provided argument or the filename of the input WAV file
        savename = args.savename
        if(not savename):
            savename = Path(args.path).parts[-1].split('.')[0]


        print("Transcribing {} with model {}".format(args.path, args.model))
        res_dict = transcribe_wav(args.path, args.model)
        print('Transcription Complete. Saving Result...')

        # Convert the segments to a DataFrame and save as CSV
        segDF = segment_to_dataframe(res_dict['segments'])
        segDF.to_csv(os.path.join(args.savepath, savename + '.csv'))

        # If requested, segment the audio and save the segments as WAV files
        if(args.segment):
            segment_audio(segDF, args.path, args.savepath, lead=0, tail=0)
            




