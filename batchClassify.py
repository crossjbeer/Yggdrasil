import os
import re
import argparse
import librosa 
import numpy as np 
from pathlib import Path 
import pandas as pd 
import mysql.connector

from resemblyzer.audio import preprocess_wav 
from resemblyzer.voice_encoder import VoiceEncoder


def make_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--path', help='Pathway to directory with split wav files', required=True)
    parser.add_argument('-n', '--names', help='List of names', nargs='+', required=True)
    parser.add_argument('-sw', '--speakerWav', help='Pathway to speaker sample directory', required=True)
    parser.add_argument('-u', '--user', help='MySQL user', required=True)
    parser.add_argument('-pw', '--password', help='MySQL password', required=False)
    parser.add_argument('-ho', '--host', help='MySQL host', required=True)
    parser.add_argument('-d', '--database', help='MySQL database', required=True)
    parser.add_argument('-s', '--session', help='Session ID', required=True)
    return parser

def main():
    parser = make_parser()
    args = parser.parse_args()

    # Get the command-line arguments
    path = args.path
    names = args.names
    speakerWav = args.speakerWav
    user = args.user
    password = args.password
    host = args.host
    database = args.database
    session = args.session


    try:
        cnx = mysql.connector.connect(
            user=user,
            password=password,
            host=host,
            database=database
        )

        cursor = cnx.cursor()
    except Exception as e:
        print("MySQL Connection Failed: [{}]".format(e))
        exit()

    if(not os.path.exists(path)):
        print("Improper Path: {}".format(path))
        exit()

    query = "SELECT start, end, session_id FROM transcript WHERE session = %s"
    values = (session,)

    try:
        cursor.execute(query, values)

        # Fetch all the segmentation rows for the specified session ID
        segmentation_rows = cursor.fetchall()
    except Exception as e:
        print("Problem accessing database: [{}]".format(e))
        exit()

    try:
        fullWav, _ = librosa.load(path, sr=None)
    except:
        print("Failed to load wav [{}]...".format(path))
        exit()


    speaker_wavs = []
    for name in names:
        speaker_wavs.append(preprocess_wav(Path(os.path.join(speakerWav, name+'.wav'))))

    encoder = VoiceEncoder('cpu')
    speaker_embeds = [encoder.embed_utterance(speaker_wav) for speaker_wav in speaker_wavs]

    for segment_row in segmentation_rows:
        start_time = segment_row[0]
        end_time = segment_row[1]
        id = segment_row[2]

        # Segment the WAV file based on the start and end times
        segmented_wav = fullWav[int(start_time * 16000):int(end_time * 16000)] ## NOTE : FOR STANDARD 16kHz wav | TO DO : Add as Commandline arg

        try:
            preprocessedWav = preprocess_wav(segmented_wav)
        except:
            print("Failed to preprocess the segment...")
            continue

        try:
            _, cont_embeds, _ = encoder.embed_utterance(preprocessedWav, return_partials=True, rate=16)
        except:
            print("Failed to embed the segment...")
            continue

        # Perform classification on the segment using the modified code
        similarity_dict = {name: cont_embeds @ speaker_embed for name, speaker_embed in zip(names, speaker_embeds)}

        means = [np.mean(similarity_dict[name]) for name in similarity_dict]

        meanMax = np.argmax(means)
        bestName = names[meanMax]

        try:
            query = "UPDATE transcript SET class = %s WHERE session_id = %s"
            values = (bestName, id)
            cursor.execute(query, values)
            cnx.commit()
            print("Classified id {} as {}".format(id, bestName))
        except Exception as e:
            print("Unable to update classification for {} ({}, {})".format(session, start_time, end_time))
            print("Error: {}".format(e))





if __name__ == "__main__":
    main()


