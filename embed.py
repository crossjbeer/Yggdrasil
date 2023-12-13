import pinecone
import os
import argparse
import openai
import datetime as dt 
import numpy as np 

from tokenizer import Tokenizer
from scripter import Scripter, NAMEDICT

openai.api_key = os.getenv('OPENAI_AUTH')
pinecone.init(api_key=os.getenv('PINECONE_AUTH'), environment="asia-southeast1-gcp-free")


def make_parser():
    # Create an argument parser
    parser = argparse.ArgumentParser(description='Process transcribed, classified session audio for Vector DB.')

    parser.add_argument("-s", '--session', type=str, help='Session Code', default=None, required=False)
    parser.add_argument('-sn', '--session_name', type=str, help='Session Name', default=None)
    parser.add_argument('-wm', '--whispermodel', help='Name of the whisper model used to transcribe (for session id)', default='base.en', type=str)

    parser.add_argument('-p', '--pinecone', help='Upload vectors to pinecone db', action='store_true')
    parser.add_argument('-pi', '--pinecone_index', help='Index for Vectors', type=str, default='yggy')
    parser.add_argument('-pns', '--namespace', help='Pinecone namespace to add vectors to', default='')

    parser.add_argument('--path', help='Path to .txt to embed', default='', required=False)

    parser.add_argument('--host', help='Database host', default='localhost')
    parser.add_argument('--user', help='Database user', default='ygg')
    parser.add_argument('--password', help='Database password', default='')
    parser.add_argument('--table', help='Database table', default='transcript')
    parser.add_argument('--database', help='Database name', default='yggdrasil')

    parser.add_argument('--embedding_model', help='Embedding Model', default='text-embedding-ada-002')

    parser.add_argument('--startingline', help='Line of session to begin from', default=0, type=int)
    parser.add_argument('--cols', help='Columns to embed from mysql table', nargs="+", type=list, default=['class', 'text'], required=False)
    parser.add_argument('--tossno', help='Toss out segments unrelated to DND using GPT 3.5 as a descriminator', action='store_true')
    parser.add_argument('--tokenlim', help='Replaces batch size + stride. Pulls lines in order until a token cost has been exceeded.', default=500, type=int)
    
    parser.add_argument('--clean', help='Clean text to anonymized and stripped', action='store_true')
    parser.add_argument("--stopword", help='Remove stopwords', action='store_true')

    parser.add_argument('--lag', help='Number of lines to lag behind token chunk calculation', default=0, type=int)
    parser.add_argument('--lead', help='Number of lines to lead ahead token chunk calculation', default=0, type=int)

    parser.add_argument('--halt', action="store_true", help='Will pause before sending each prompt')

    return(parser)


def create_embedding(text, embedding_model='text-embedding-ada-002'):
    """
    Create the embedding for the given text.

    Args:
        text (str): Text to be embedded.

    Returns:
        dict: Embedding response.
    """
    try:
        response = openai.Embedding.create(
            input=text,
            model=embedding_model
        )
        return response
    except Exception as e:
        print("Problem building embedding for text:")
        print(text)
        print(e)
        return None

def upload_to_pinecone(index, cid, embedding, metadata, namespace=''):
    """
    Upload the embeddings to Pinecone database.

    Args:
        index (pinecone.Index): Pinecone index object.
        cid (str): Unique identifier.
        embeddings (list): List of embeddings to be uploaded.
    """

    try:
        index.upsert(
            vectors = [
                {
                    'id':cid,
                    'values':embedding, 
                    'metadata':metadata
                }
            ],
            namespace=namespace
        )
    except Exception as e:
        print("Error uploading embeddings for cid: {}".format(cid))
        print(e)


def related_to_dnd(str_rows):
    model = 'gpt-3.5-turbo-0613'
    messages = [
        {'role':'system', 'content':'You are a discriminator you will be asked a yes or no question about text. Respond with yes or no.'},
        {'role':'user', 'content':'Are the following rows of a transcript related to DND? Do they mention anything fantastical or out of ordinary conversation?'},
    ]

    messages += [{'role':'user', 'content':msg} for msg in str_rows]
    messages += [{'role':'assistant', 'content':'(yes/no): '}]

    gpt_response = openai.ChatCompletion.create(
        model=model,
        messages=messages
    )

    return(gpt_response['choices'][0]['message']['content'].lower() == 'yes')

def process_script(args, df, script, index=None):
    i = args.startingline
    df = df.iloc[args.startingline:]
    for i, j in script.getAllTokenChunkBounds(df, args.tokenlim):
        i = max(0, i-args.lag)
        j = min(len(df)-1, j+args.lead)

        str_rows = script.getStrRows(df, i, j-i)
        firstID = i

        print('*********************************************')
        print('\n'.join(str_rows))
        print("TOKENS: {}".format(script.tizer.calculate_tokens('\n'.join(str_rows))))

        if(args.halt):
            input('EMBED? ^')

        if(args.tossno):
            if(not related_to_dnd(str_rows)):
                continue

        embed_response = create_embedding("\n".join(str_rows), args.embedding_model)
        embed = embed_response['data'][0]['embedding']

        cid = "[{}]_{}_{}".format(args.path.split('/')[-1].split('.')[0], firstID, j-i)
        print("ID: {}".format(cid))
        
        if(args.halt):
            input()

        if(index):
            upload_to_pinecone(index, cid, embed, {}, args.namespace)

    return()

        
def make_arg_dict(args, avails=['session', 'session_name']):
    argDict = {}

    for avail in avails:
        if(avail in args and vars(args)[avail] is not None):
            argDict[avail] = vars(args)[avail]

    return(argDict)


def main():
    parser = make_parser() 
    args = parser.parse_args() 

    script = Scripter()
    script.loadTokenizer('ada-002')
    if(args.path and os.path.exists(args.path)):
        df = script.loadTxt(args.path)
    else:
        script.connectMySQL(args.host, args.database, args.user, args.password)
        df = script.loadMySQL(args.table, make_arg_dict(args))

    if(args.clean):
        df_clean = script.cleanDFPipe(df, stopword=args.stopword)

    pinecone_index = None 
    if(args.pinecone):
        pinecone_index = pinecone.Index(args.pinecone_index)

    print("Processing...")
    process_script(args, df_clean, script, pinecone_index)



if __name__ == '__main__':
    main() 
