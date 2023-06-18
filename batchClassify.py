import os
import re
import argparse
import librosa 
import numpy as np 
from pathlib import Path 
import pandas as pd 

from resemblyzer.audio import preprocess_wav 
from resemblyzer.voice_encoder import VoiceEncoder


def make_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--path', help='Pathway to directory with split wav files', required=True)
    parser.add_argument('-csvp', '--csvpath', help='Pathway to .csv to save classification information', required=True, type=str, default=None)
    parser.add_argument('-n', '--names', help='List of names', nargs='+', required=True)
    parser.add_argument('-sw', '--speakerWav', help='Pathway to speaker sample directory', required=True)
    #parser.add_argument('-o', '--output', help='Pathway to save directory', required=True)
    #parser.add_argument('-sl', '--segLen', help='Segment Length for Wav Breakdown (Defaut = 3(mins))', default=3, type=float)
    return parser


def main():
    parser = make_parser()
    args = parser.parse_args()

    # Get the command-line arguments
    path = args.path
    csvpath = args.csvpath
    names = args.names
    speakerWav = args.speakerWav
    #output = args.output
    #segLen = args.segLen

    if(not os.path.exists(path)):
        print("Improper Path: {}".format(path))
        exit()

    if(not os.path.exists(csvpath)):
        print("Improper csvpath: {}".format(csvpath))
        exit()

    # Get a list of split wav files in the specified directory
    wav_files = [f for f in os.listdir(path) if re.match(r'split_\d+\.wav', f)]

    if(not len(wav_files)):
        print("No .wav @ {}".format(path))

    speaker_wavs = []
    for name in names:
        speaker_wavs.append(preprocess_wav(Path(os.path.join(speakerWav, name+'.wav'))))

    encoder = VoiceEncoder('cpu')
    speaker_embeds = [encoder.embed_utterance(speaker_wav) for speaker_wav in speaker_wavs]

    classificationDict = {}
    for wf in wav_files:
        try:

            fpath = os.path.join(path, wf)
            fullWav, _ = librosa.load(fpath, sr=None)
        except:
            print("Failed to load {}...".format(wf))
            continue

        try:
            preprocessedWav = preprocess_wav(fullWav)
        except:
            print("Failed to Preprocess {}".format(wf))
            continue 

        try:
            _, cont_embeds, wav_splits = encoder.embed_utterance(preprocessedWav, return_partials=True, rate=16)
        except:
            print("Failed to embed {}".format(wf))
            continue 

        similarity_dict = {name : cont_embeds @ speaker_embed for name, speaker_embed in zip(names, speaker_embeds)}

        means = [np.mean(similarity_dict[name]) for name in similarity_dict]

        meanMax = np.argmax(means)
        bestName = names[meanMax]

        classificationDict[wf] = bestName 
        print("[{}] Classifying as {}".format(wf, bestName))

    csv = pd.read_csv(csvpath, header=0, index_col=0)
    csv.index = range(len(csv))

    keys = list(classificationDict.keys())
    vals = [classificationDict[k] for k in keys]
    keys = [int(key.split("_")[1].split(".")[0]) for key in keys]

    newDict = {key - 1 : val for key, val in zip(keys, vals)}
    newcsv = pd.DataFrame().from_dict(newDict, orient='index')

    csv.insert(4, 'class', newcsv)
    csv.to_csv(csvpath)





if __name__ == "__main__":
    main()


