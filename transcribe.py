import whisper as wisp
import argparse
import os
import json
import soundfile as sf
import pandas as pd
import mysql.connector
import datetime as dt

def make_parser():
    parser = argparse.ArgumentParser(description='Whisper ASR Transcription')

    parser.add_argument('-p', '--path', help='Path to the .wav file', required=True)
    parser.add_argument('-m', '--model', help='Whisper Model to Use [tiny.en, small.en, base.en, medium.en, large.en]', default='base')
    parser.add_argument('--segment', help='option to segment provided .wav file and save to savepath', action='store_true')
    parser.add_argument('-sp', '--savepath', help='Path to save segmented audio', type=str)
    parser.add_argument('--host', help='MySQL host', default='localhost', required=False)
    parser.add_argument('--db', help='MySQL database name', required=False)
    parser.add_argument('--user', help='MySQL username', required=False)
    parser.add_argument('--password', help='MySQL password', required=False)
    parser.add_argument('--table', help='Table with transcript', default='transcript')
    parser.add_argument('--session', help='Session name', required=False)
    parser.add_argument('--lang', default='en', help='Language to Transcribe', required=False)

    return(parser)

def load_whisper_model(model):
    try:
        return wisp.load_model(model)
    except Exception as e:
        raise ValueError("Failed to load Whisper model.") from e

def load_audio_file_whisper(wav):
    try:
        return wisp.load_audio(wav)
    except Exception as e:
        raise ValueError("Failed to load audio file.") from e

def transcribe_audio(model, audio):
    return wisp.transcribe(model, audio)

def save_transcription_as_json(res_dict, path):
    segs = res_dict['segments']
    path = os.path.join(path, 'res.json')
    with open(path, 'w') as of:
        json.dump(segs, of)

def segment_to_dataframe(segments):
    allSegments = pd.DataFrame()
    for i, segment in enumerate(segments):
        segment['tokens'] = [segment['tokens']]
        segment = pd.DataFrame(index=[i]).from_dict(segment, orient='columns')
        allSegments = pd.concat([allSegments, segment], axis=0)
    return allSegments

def segment_audio(segDF, wav, savepath, lead=0, tail=0):
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

def save_transcription_to_mysql(res_dict, mysql_config, table, session, whispermodel):
    segments = res_dict['segments']

    try:
        sql = True
        connection = mysql.connector.connect(**mysql_config)
        cursor = connection.cursor()
    except:
        print("no sql connection")
        sql = False

        # Insert each segment into the MySQL table
    for i, segment in enumerate(segments):
        start = segment['start']
        end = segment['end']
        text = segment['text']
        now = dt.datetime.now()
        session_id = i+1

        insert_query = "INSERT INTO " + table + " (session_id, session, whisper, text, start, end, upload) VALUES (%s, %s, %s, %s, %s, %s, %s)"

        cursor.execute(insert_query, (session_id, session, whispermodel, text, start, end, now))

    if(sql):
        connection.commit()
        print("Transcription data saved to MySQL.")

        # Close the cursor and connection
        cursor.close()
        connection.close()

def main():
    parser = make_parser()
    args = parser.parse_args()

    # Check if the provided path exists
    if not os.path.exists(args.path):
        raise ValueError("Input file path does not exist.")
    if not args.path.endswith('.wav'):
        raise ValueError("Input file [{}] is not a .wav!".format(args.path))

    if args.segment:
        if not args.savepath:
            raise ValueError("<savepath> must be provided as arg if segmentation is requested...")
        elif not os.path.exists(args.savepath):
            try:
                os.makedirs(args.savepath)
            except Exception as e:
                print("Unable to build save path [{}]...{}".format(args.savepath, e))
                exit()

    mysql_config = {
        'host': args.host,
        'database': args.db,
        'user': args.user,
        'password': args.password
    }

    print("Transcribing {} with Model {}".format(args.path, args.model))
    model = load_whisper_model(args.model)
    audio = load_audio_file_whisper(args.path)
    res_dict = transcribe_audio(model, audio)
    print('Transcription Complete. Saving Result...')

    #save_transcription_as_json(res_dict, args.savepath)

    # Save the transcription to MySQL
    if args.db:
        save_transcription_to_mysql(res_dict, mysql_config, args.table, args.session, args.model)

    # If requested, segment the audio and save the segments as WAV files
    segDF = segment_to_dataframe(res_dict['segments'])

    if args.savepath:
        segDF.to_csv(os.path.join(args.savepath, 'res.csv'))

    if args.segment:
        segment_audio(segDF, args.path, args.savepath, lead=0, tail=0)


if __name__ == '__main__':
    main() 

    #main(args)