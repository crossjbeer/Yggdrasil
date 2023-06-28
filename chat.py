import openai
import os 
import argparse 
import pinecone 
import pandas as pd 
import numpy as np 
import mysql.connector

from chatter import Colorcodes, Chatter
from scripter import Scripter

openai.api_key = os.getenv('OPENAI_AUTH')

# Alternatively just set your own api key (just don't upload to git!)
pinecone.init(api_key = '27f2b80f-96a2-4c4f-baba-262615e29ac2', environment='asia-southeast1-gcp-free')

INDEX = pinecone.Index('ygg')
COLORCODE = Colorcodes()

def embeddingToText(path):
    res = pd.read_csv(path, header=0)

    return({res['index'].values[i] : res['text'].values[i] for i in range(len(res))})

def estimateTokens(s, charPerToken = 4):
    return(len(s) / charPerToken)


def main():
    messages = [{'role':'system', 'content':"""You are the Lore Master. You preside over the sacred transcript of a dungeons and dragons campaign.
                                            Your job is to be the ultimate dnd assistant. The user may ask you any variety of questions related to dungeons and dragons. 
                                            This can include asking to help build a village, design a character, assist with roleplay, or produce writing materials. 

                                            You will be provided with a section of the transcript related to the question the user has asked. Use this transcript and any 
                                            background knowledge you may have to answer the user's question as well as you can. 

                                            DO NOT MAKE UP ANYTHING UNLESS SPECIFICALLY ASKED. Use the information provided to answer questions and, if the information is 
                                            not sufficient, do not resort to making up information. Simply report that no other relevant information was provided.
                                            
                                            Here are the speaker codes, names, and character / role:
                                            <1> cro: Crossland (DM) 
                                            <2> ric: Richard (Likkvorn)
                                            <3> let: Leticia (Russet Crow)
                                            <4> sim: Simon (Lief) 
                                            <5> ben: Ben (Oskar) 
                                            <6> kacie: Kacie (Isra).
                                            """}]
    

    parser = argparse.ArgumentParser()
    parser.add_argument('-q', '--query', help='Query for Chat GPT', type=str, default=None, required=False)
    parser.add_argument('-m', '--model', help='Open AI model to use [gpt3.5-turbo, gpt4]', type=str, default='gpt-4')
    parser.add_argument('-n', '--nvector', help='Number of vectors to query', type=int, default=5)
    parser.add_argument('--host', help='Database host', type=str, default='localhost')
    parser.add_argument('--user', help='Database user', type=str, default='ygg')
    parser.add_argument('--db', help='Database name', type=str, default='yggdrasil')
    parser.add_argument('--password', help='Database password', type=str, default=None)


    args = parser.parse_args() 

    db_connection = mysql.connector.connect(
        host=args.host,
        user=args.user,
        password=args.password,
        database=args.db
    )

    if not db_connection.is_connected():
        # Close the database connection
        print(f"{COLORCODE.orange}Cannot connect to MySQL database{COLORCODE.reset}\n")

    else:
        print(f"{COLORCODE.orange}Connected to MySQL database{COLORCODE.reset}\n")
        # Create a cursor object
        cursor = db_connection.cursor()

    prompt = args.query
    if(not prompt or not len(prompt)):
        prompt = input(f"{COLORCODE.blue}Prompt> {COLORCODE.reset}")
        print()

    print(f"{COLORCODE.red}Converting query into Embedding...{COLORCODE.reset}")
    response = openai.Embedding.create(
            input=prompt,
            model='text-embedding-ada-002'
    )
    embeddings = response['data'][0]['embedding']
    print(f"{COLORCODE.orange}Embedding Complete{COLORCODE.reset}\n")

    print(f"{COLORCODE.red}Using Embedding to Query Pinecone for top {args.nvector} Vectors...{COLORCODE.reset}")
    relatedVectors = INDEX.query(
        top_k=args.nvector,
        vector=embeddings ,
        include_values=True
    )
    print(f"{COLORCODE.orange}Pinecone Query Complete{COLORCODE.reset}\n")

    relatedID = [i['id'] for i in relatedVectors['matches']]

    script = Scripter()

    session_bs_index = []
    for id in relatedID:
        session_bs_index.append((id.split('_')[0], int(id.split('_')[3][2:]), int(id.split('_')[5])))

    unique_sessions = np.unique([i[0] for i in session_bs_index])
    sessionToQuery = {}
    
    for s in unique_sessions:
        indices = [i[2] for i in session_bs_index if i[0] == s]
        bs      = [i[1] for i in session_bs_index if i[0] == s]

        if(len(indices) == 1):
            sessionToQuery[s] = [(indices[0], indices[0] + bs[0])]
            continue

        bs = [x for _, x in sorted(zip(indices, bs))]
        indices = sorted(indices)

        """
        querys = []
        start_ind = None
        stop_ind = None 
        for i in range(len(indices)-1):
            cind, nind = indices[i], indices[i+1]
            cb, nb = bs[i], bs[i+1]

            if(not start_ind):
                start_ind = cind

            if(cind + cb <= nind):
                querys.append((start_ind, cind+cb))
                stop_ind = None 
            else:
                stop_ind = nind + nb

        if(stop_ind):
            querys.append((start_ind,))
        """

        querys = [] 
        i = 0 
        start_ind = None 
        while i < len(indices)-1:
            cind, nind = indices[i], indices[i+1]
            cb, nb = bs[i], bs[i+1]

            if(not start_ind):
                start_ind = cind 

            if(cind + cb <= nind):
                querys.append((start_ind, cind+cb))
                start_ind = None 
                i += 1
            
            else:
                indices[i] = nind
                bs[i] = nb 

                indices.pop(1)
                bs.pop(1)

        querys.append((start_ind, indices[0] + bs[0]))
        sessionToQuery[s] = querys

    allText = ""
    for session in sessionToQuery:
        c_query = sessionToQuery[session]

        for start, end in c_query:
            print("[{}] Pulling Lines {} -> {}".format(session, start, end))
            query = "SELECT class, text FROM transcript WHERE session = %s AND session_id > %s AND session_id < %s ORDER BY session_id ASC;"
            cursor.execute(query, (session, start, end))

            rows = cursor.fetchall()
            row_txt = script.combineRowList(rows)

            allText += '\n' + row_txt

    print()
    messages = [
            {'role':'user', 'content':'Context:'},
            {'role':'user', 'content':allText},
            {'role':'user', 'content':'User Query:'}
        ]
    
    chat = Chatter(args.model)
    chat.chat(prompt, True, messages)
    

if (__name__ == "__main__"):
    main()