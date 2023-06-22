"""
This code should be used to interact with the labeled, transcribed session information.

Currently, this is configured to work with .csv representations of said output, but I plan to integrate
mysql into the stack.

"""


import pinecone
import os  
import argparse
import pandas as pd 
import openai

openai.api_key = os.getenv('OPENAI_AUTH')
pinecone.init(api_key=os.getenv('PINECONE_AUTH'), environment="asia-southeast1-gcp-free")

def buildTextList(path):
    info = pd.read_csv(path, index_col=0, header=0)

    classText = info.apply(lambda row: str(row['class']) + ": " + str(row['text']), axis=1).to_list()    
    return(classText)


if __name__ == '__main__':
    # Create an argument parser
    parser = argparse.ArgumentParser(description='Process transcribed, classified session audio for Vector DB.')
    
    # Add the command-line arguments
    parser.add_argument('-p', '--path', type=str, help='Path to the CSV file containing columns [class, text]')
    parser.add_argument('-sp', '--savepath', type=str, help='Path to save the vector -> text combination object')
    parser.add_argument('-sn', '--sessionname', type=str, help='Session Name', default=None)
    parser.add_argument('-wm', '--whispermodel', help='Name of the whisper model used to transcribe (for session id)', default='base.en', type=str)
    parser.add_argument('-sl', '--segmentlen', help='Segment len used in voice classification', type=int, default=3)
    parser.add_argument('-bs', '--batchsize', type=int, help='Batch size for text ingestion', default=5)
    parser.add_argument('-st', '--stride', type=int, help='Number of rows to progress with each new batch', default=1)
    parser.add_argument('--pinecone', help='Upload vectors to pinecone db', action='store_true')

    # Parse the command-line arguments
    args = parser.parse_args()

    # Check if the path exists
    if not os.path.exists(args.path):
        print(f"Error: The path '{args.path}' does not exist.")
        exit()
    
    # Create the directory for savepath if it doesn't exist
    save_dir = os.path.dirname(args.savepath)
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    text = buildTextList(args.path)

    if(args.pinecone):
        index = pinecone.Index('ygg')

    df_cols = ['index', 'text', 'embedding', 'model', 'prompt_tokens', 'total_tokens']
    res = pd.DataFrame(columns=df_cols)
    for i in range(0, len(text), args.stride):
        c_text = text[i : min(len(text), i + args.batchsize)]

        full_str = '\n'.join(c_text)

        cid = "{}_{}_SL{}_BS{}_STR{}_{}".format(args.sessionname, args.whispermodel, args.segmentlen, args.batchsize, args.stride, i)
        
        try:
            response = openai.Embedding.create(
                input=full_str,
                model='text-embedding-ada-002'
            )
        except Exception as e :
            print("Problem building embedding for {}".format(cid))
            print(e)
            continue 

        embeddings = response['data'][0]['embedding']
        model = response['model']
        prompt_tokens = response['usage']['prompt_tokens']
        total_tokens = response['usage']["total_tokens"]

        tdf = pd.DataFrame([[i, full_str, embeddings, model, prompt_tokens, total_tokens]], 
                           columns=['index', 'text', 'embedding', 'model', 'prompt_tokens', 'total_tokens'], index=[i])

        res = pd.concat([res, tdf], axis=0)
        res.to_csv(os.path.join(save_dir, 'BS{}_STR{}.csv'))

        if(args.pinecone):
            try:
                upsert_response = index.upsert(
                    vectors = [
                        (
                            cid,
                            embeddings
                        )
                    ]
                )
            except Exception as e:
                print("Error uploading {}".format(cid))
                print(e)

    pinecone.deinit()





    


