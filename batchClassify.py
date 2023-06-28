import os
import argparse
import librosa 
import numpy as np 
from pathlib import Path 
import mysql.connector

from resemblyzer.audio import preprocess_wav 
from resemblyzer.voice_encoder import VoiceEncoder


def make_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--path', help='Pathway to directory with split wav files', required=True)
    parser.add_argument('-n', '--names', help='List of names', nargs='+', required=True)
    parser.add_argument('-sw', '--speakerWav', help='Pathway to speaker sample directory', required=False, default='./speaker_samples/')
    parser.add_argument('-u', '--user', help='MySQL user', required=False, default='ygg')
    parser.add_argument('-pw', '--password', help='MySQL password', required=False)
    parser.add_argument('-ho', '--host', help='MySQL host', required=False, default='localhost')
    parser.add_argument('-d', '--database', help='MySQL database', required=False, default='yggdrasil')
    parser.add_argument('-s', '--session', help='Session ID', required=True)
    parser.add_argument('-sr', '--samplerate', help='Sample rate for .wav', default=16000)
    parser.add_argument('--noupload', help='Will avoid uploading new classifications', action='store_true')
    parser.add_argument('-sid', '--startingid', help='ID In Database to start @ when classifying', type=int, default=0)
    return parser

def connect_to_mysql(user, password, host, database):
    try:
        cnx = mysql.connector.connect(
            user=user,
            password=password,
            host=host,
            database=database
        )
        cursor = cnx.cursor()
        return cnx, cursor
    except Exception as e:
        print("MySQL Connection Failed: [{}]".format(e))
        exit()

def check_path_exists(path):
    if not os.path.exists(path):
        print("Improper Path: {}".format(path))
        exit()

    elif(not path.endswith('.wav')):
        print("Given Path [{}] not .wav".format(path))
        exit() 

def load_full_wav(path):
    try:
        full_wav, _ = librosa.load(path, sr=None)
        return full_wav
    except:
        print("Failed to load wav [{}]...".format(path))
        exit()

def fetch_segmentation_rows(cursor, session, id):
    query = "SELECT start, end, session_id FROM transcript WHERE session = %s AND session_id >= %s"
    values = (session, id,)

    try:
        cursor.execute(query, values)
        return cursor.fetchall()
    except Exception as e:
        print("Problem accessing database: [{}]".format(e))
        exit()

def preprocess_speaker_wavs(speakerWav, names):
    speaker_wavs = []
    failure = False 

    for name in names:
        speaker_path = os.path.join(speakerWav, name + '.wav')
        if(not os.path.exists(speaker_path)):
            print("Speaker Path [{}] Doesn't Exist...".format(speaker_path))
            failure = True 

        speaker_wavs.append(preprocess_wav(Path(speaker_path)))

    if(failure):
        print("Speaker Wav Ingestion Failed...")
        exit()

    return speaker_wavs

def embed_speaker_wavs(encoder, speaker_wavs):
    speaker_embeds = [encoder.embed_utterance(speaker_wav) for speaker_wav in speaker_wavs]
    return speaker_embeds

def segment_wav(fullWav, start_time, end_time):
    segmented_wav = fullWav[int(start_time * 16000):int(end_time * 16000)]  # Standard 16kHz wav
    return segmented_wav

def preprocess_segment(segmented_wav):
    try:
        preprocessed_wav = preprocess_wav(segmented_wav)
        return preprocessed_wav
    except:
        print("Failed to preprocess the segment...")
        return None


def embed_segment(encoder, preprocessed_wav):
    try:
        _, cont_embeds, _ = encoder.embed_utterance(preprocessed_wav, return_partials=True, rate=16)
        return cont_embeds
    except:
        print("Failed to embed the segment...")
        return None

def classify_segment(names, speaker_embeds, cont_embeds):
    similarity_dict = {name: cont_embeds @ speaker_embed for name, speaker_embed in zip(names, speaker_embeds)}
    means = [np.mean(similarity_dict[name]) for name in similarity_dict]
    meanMax = np.argmax(means)
    bestName = names[meanMax]
    return bestName


def update_classification(cursor, cnx, session, start_time, end_time, bestName, id):
    try:
        query = "UPDATE transcript SET class = %s WHERE session_id = %s"
        values = (bestName, id)
        cursor.execute(query, values)
        cnx.commit()
        print("Classified id {} as {}".format(id, bestName))
    except Exception as e:
        print("Unable to update classification for {} ({}, {})".format(session, start_time, end_time))
        print("Error: {}".format(e))

def classify(cnx, cursor, session, segmentation_rows, fullWav, encoder, names, speaker_embeds, noupload):
    namelist = []
    for segment_row in segmentation_rows:
        start_time = segment_row[0]
        end_time = segment_row[1]
        id = segment_row[2]

        # Segment the WAV file based on the start and end times
        segmented_wav = segment_wav(fullWav, start_time, end_time)

        # Preprocess the segment
        preprocessed_wav = preprocess_segment(segmented_wav)

        if preprocessed_wav is None:
            continue

        # Embed the segment
        cont_embeds = embed_segment(encoder, preprocessed_wav)

        # Perform classification on the segment
        bestName = classify_segment(names, speaker_embeds, cont_embeds)
        namelist.append((id, bestName))

        # Update the classification in the database
        if(noupload):
            continue 

        update_classification(cursor, cnx, session, start_time, end_time, bestName, id)

    return(namelist)


def main():
    parser = make_parser()
    args = parser.parse_args()
  
    path       = args.path
    names      = args.names
    speakerWav = args.speakerWav
    user       = args.user
    password   = args.password
    host       = args.host
    database   = args.database
    session    = args.session

    # Check if the provided path exists
    check_path_exists(path)

    # Load the full WAV file
    fullWav = load_full_wav(path)

    # Connect to MySQL
    cnx, cursor = connect_to_mysql(user, password, host, database)

    # Fetch segmentation rows from the database
    segmentation_rows = fetch_segmentation_rows(cursor, session, args.startingid)

    # Preprocess speaker WAV files
    speaker_wavs = preprocess_speaker_wavs(speakerWav, names)

    # Initialize the voice encoder
    encoder = VoiceEncoder('cpu')

    # Embed the speaker WAV files
    speaker_embeds = embed_speaker_wavs(encoder, speaker_wavs)

    print("Classifying...")
    nl = classify(cnx, cursor, session, segmentation_rows, fullWav, encoder, names, speaker_embeds, args.noupload)

    with open("./tests/20230330/new_samples/names.txt", 'w') as wf:
        for i, l in enumerate(nl):
            wf.write("{}. {} ({})\n".format(i, l[0], l[1]))

    cursor.close()
    cnx.close()


if __name__ == "__main__":
    main()