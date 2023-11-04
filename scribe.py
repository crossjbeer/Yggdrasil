import argparse 
import os 
import subprocess 
import datetime as dt 


def make_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--path', help='Path to folder with .mkv files', required=True)
    parser.add_argument('--session', help='Session name', required=True)
    parser.add_argument('--host', help='Database host', default='localhost')
    parser.add_argument('--user', help='Database user', default='ygg')
    parser.add_argument('--password', help='Database password', default='')
    parser.add_argument('--table', help='Database table', default='transcript')
    parser.add_argument('--database', help='Database name', default='yggdrasil')
    parser.add_argument('--whisper_model', help='Whisper model', default='medium')
    parser.add_argument('--speaker_wav_path', help='Speaker wav path', default='./speaker_samples/')
    parser.add_argument('--speaker_names', help='Speaker names', nargs='+', required=True)
    parser.add_argument('--session_name', help='Name for session in MySQL. Defaults to session code', type=str, required=False, default="")

    parser.add_argument("--no_ingestvid", help='Turn on to avoid ingesting videos using scribe...', action='store_true')
    parser.add_argument("--no_transcribe", help='Turn on to avoid transcribing with scribe', action='store_true')
    parser.add_argument('--no_classify', help='Turn on to avoid classifying audio with scribe', action='store_true')
    return parser


def main():
    parser = make_parser()
    args = parser.parse_args()

    session_name = args.session_name
    if(not len(session_name)):
        session_name = args.session 

    print("*"*100)
    print("Running for Session [{}] Session Name [{}] | Whisper Model [{}]".format(args.session, args.session_name, args.whisper_model))
    print("*"*100)
    print()

    if(not args.no_ingestvid):
        print("Ingesting Videos...")
        subprocess.call(['python3', 'ingestvid.py', '-p', os.path.join(args.path, args.session), '-sp', os.path.join(args.path, args.session), '-sn', args.session])
    
    if(not args.no_transcribe):
        print("Transcribing Audio")
        subprocess.call(['python3', 'transcribe.py', '-p', os.path.join(args.path, args.session, args.session+'.wav'), '-m', args.whisper_model, '--host', args.host, '--db', args.database, '--user', args.user, '--password', args.password, '--session', args.session, '--table', args.table, '--session_name', session_name])
    
    if(not args.no_classify):
        print("Classifying Audio")
        subprocess.call(['python3', 'classify.py', '-p', os.path.join(args.path, args.session, args.session + '.wav'), '-sw', args.speaker_wav_path, '-u', args.user, '-pw', args.password, '-ho', args.host, '-d', args.database, '-n', *args.speaker_names, '-s', args.session, '--session_name', session_name, '--whisper', args.whisper_model, '--table', args.table])

if(__name__ == "__main__"):
    main()
