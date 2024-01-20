import os
import argparse
from openai import OpenAI
import numpy as np 
from pgvector.psycopg2 import register_vector

from scripter import Scripter
from parsers import make_parser_sql
from pg_chat import connect

def make_parser():
    # Create an argument parser
    parser = argparse.ArgumentParser(description='Embed a note')

    parser = make_parser_sql()
    parser.description = 'Embed a Note'

    parser.add_argument("-p", '--path', help='Path to .txt to embed', default='', required=False)
    parser.add_argument('--startingline', help='Line to start', default=0)
    parser.add_argument('--embedding_model', help='Embedding Model', default='text-embedding-ada-002')
    parser.add_argument('-tl', '--tokenlim', help='Replaces batch size + stride. Pulls lines in order until a token cost has been exceeded.', default=500, type=int)
    parser.add_argument('--clean', help='Clean text to anonymized and stripped', action='store_true')
    parser.add_argument("--stopword", help='Remove stopwords', action='store_true')
    parser.add_argument('--halt', action="store_true", help='Will pause before sending each prompt')
    parser.add_argument('--lag', default=0, help='Lag between token chunks', type=int)
    parser.add_argument("--namespace", default='note', help='Namespace for embedding', type=str)

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
        client = OpenAI(api_key=os.environ.get("OPENAI_AUTH"))
        response = client.embeddings.create(input=text, model=embedding_model)
        return response.model_dump()
    
    except Exception as e:
        print("Problem building embedding for text:")
        print(text)
        print(e)
        return None

def embed(text, embedding_model='text-embedding-ada-002'):
    embed_response = create_embedding(text, embedding_model)
    return(embed_response['data'][0]['embedding'])


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

def pg_upload_embedding(connection, notes_table, content, note, start_line, end_line, embedding, namespace):
    cursor = connection.cursor() 
    if(not cursor):
        print("NO CURSOR")
        return(None)
    
    query = 'INSERT INTO {} (content, note, start_line, end_line, embedding, namespace) VALUES (%s, %s, %s, %s, %s, %s)'.format(notes_table)
    cursor.execute(query, (content, note, start_line, end_line, embedding, namespace,))

    connection.commit()

    return(connection)

def process_note(df, script, connection, notes_table='notes', note_title="", startingline=0, tokenlim=500, halt=False, embedding_model=None, lag=0, namespace=None, *args, **kwargs):
    if(not connection):
        exit("No Postgres Connection")


    df = df.iloc[startingline:]
    for i, j in script.getAllTokenChunkBounds(df, tokenlim, lag=lag):
        chunk = script.getDFRows(df, i, j-i)
        text = script.getText(chunk)

        if(halt):
            print('*********************************************')
            print(text)
            print("# Tokens: {}".format(script.calcTokens(text)))
            input('EMBED? ^')

        embedding = embed(text, embedding_model)

        print("{} | {} -> {}".format(note_title, i, j))
        pg_upload_embedding(connection, notes_table, text, note_title, i, j, np.asarray(embedding), namespace)

    return()
      
def main():
    parser = make_parser() 
    args = parser.parse_args() 

    script = Scripter()
    script.loadTokenizer('ada-002')
    if(args.path and os.path.exists(args.path)):
        df = script.loadTxt(args.path, True)
    else:
        exit("No note")

    df_clean = df 
    if(args.clean):
        df_clean = script.cleanDFPipe(df, stopword=args.stopword)

    args.note_title = args.path.split("/")[-1]
    try:
        connection = connect(**vars(args))
        register_vector(connection)
    except Exception as e: 
        print("Unable to open Postgres Connection...")
        exit(e)

    print(f"Processing Note [{args.note_title}]...")
    process_note(df_clean, script, connection, **vars(args))



if __name__ == '__main__':
    main() 
