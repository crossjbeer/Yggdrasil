from openai import OpenAI
import numpy as np 

from chatter import Chatter 
from tokenizer import Tokenizer 
from colorcodes import Colorcodes

from parsers import make_parser_gpt_sql
from pg_vector import grab_k
from pg_embed import create_embedding

def sortXbyY(X, Y):
    return([x for _, x in sorted(zip(Y, X))])

LORE_MASTER = """You are the LORE MASTER.
You preside a cherished campaign of Dungeons and Dragons (dnd).
Your job is to be the ultimate dnd assistant.

You have an assistant, IGOR.
IGOR will research for you, and provide you with summaries of relevant information he finds. 
Please use IGOR's summaries to inform your answers. 

You will see messages with the following structure: 
IGOR SUMMARY: <igor's summary>

USER QUERY: <user query>

Please use IGOR's summary to accurately answer the USER's query!

Remember, these notes are sacred and should be adheared to. 
Be thorough and give the user the specific detail they are interested in.   
And most importantly, be creative and have fun!"""

IGOR = """ 
You are a world-class researcher and have access to the sacred notes of a dnd campaign.
Your job is to summarize information relevant to a given USER QUERY. 

You will see information passed with the structure: 
NOTE: <Note Name>
```
Relevant information from <Note Name>...
```

USER QUERY: <question>

Please refer to the question and summarize any information relevant to that question.
"""


def organize_notes_from_vectors(vectors):
    unique_notes = np.unique(vectors['note'])

    notes = {}
    for note in unique_notes:
        content = [] 
        starting_lines = [] 
        for i in range(len(vectors['note'])):
            if(vectors['note'][i] == note):
                content.append(vectors['content'][i])
                starting_lines.append(vectors['start_line'][i])

        content = sortXbyY(content, starting_lines)
        content = "".join(content)

        msg = f"""NOTE: {note}\n\n```{content}```"""
        notes[note] = msg
        #gptb.append(chatter.getUsrMsg(msg))

    return(notes)

def ask_igor(prompt, embedder='text-embedding-ada-002', model='gpt-3.5-turbo', nvector=5, host='localhost', port='', user='crossland', password='pass', database='yggdrasil', chatter=None, igor_prompt=IGOR, verbose=False):
    color = Colorcodes()
    igor_msg = [chatter.getSysMsg(igor_prompt)] if igor_prompt else [] 

    if(not chatter):
        chatter = Chatter(model)

    if(verbose):
        print(color.pred(f"\tConverting query into Embedding with model {embedder}..."))

    embed_response = create_embedding(prompt, embedder)
    embedding = embed_response['data'][0]['embedding']

    if(verbose):
        print(color.pred(f'\tGrabbing {nvector} Associated Note Vectors'))
    vec = grab_k(embedding, k=nvector, host=host, port=port, user=user, password=password, database=database)

    igor_notes = organize_notes_from_vectors(vec)
    for note in igor_notes:
        igor_msg.append(chatter.getUsrMsg(igor_notes[note]))

    igor_msg.append(chatter.getUsrMsg('USER QUERY: {}'.format(prompt)))

    if(verbose):
        print(color.pbold(color.pred('\tSummarizing with IGOR...')))
    igor_reply = chatter.passMessagesGetReply(igor_msg)

    return(igor_reply)

def ask_loremaster(prompt, igor_reply, chatter, messages=[], loremaster_prompt = LORE_MASTER, verbose=False):
    color = Colorcodes()

    if(not len(messages)):
        messages.append(chatter.getUsrMsg(loremaster_prompt))

    loremaster_msg = f"""IGOR SUMMARY: {igor_reply}\n\nUSER QUERY: {prompt}"""
    messages.append(chatter.getUsrMsg(loremaster_msg))

    if verbose:
        print(color.pbold(color.pred('\tPassing to LORE MASTER...')))

    reply = chatter.passMessagesGetReply(messages)

    return(reply, messages)


def noting(model, query, nvector, embedder, host, port, user, password, database, lore_master=LORE_MASTER, igor=IGOR, verbose=True, *args, **kwargs):
    color = Colorcodes()
    print(color.pbold(f'~~ Chatting with {model} ~~'))
    chatter = Chatter(model)

    loremaster_msg = [] 
    prompt = query if query else chatter.usrprompt()
    while True:
        if(prompt is None):
            prompt = chatter.usrprompt()

        igor_reply = ask_igor(prompt, embedder, model, nvector, host, port, user, password, database, chatter, igor, verbose=verbose)

        loremaster_reply, loremaster_msg = ask_loremaster(prompt, igor_reply, chatter, messages=loremaster_msg, verbose=verbose)
        loremaster_msg.append(chatter.getAssMsg(loremaster_reply))

        chatter.printMessages(loremaster_msg[-2:])
        input('Continue?')

        prompt = None 




def main():
    parser = make_parser_gpt_sql()
    args = parser.parse_args() 

    noting(**vars(args))

        



if __name__ == "__main__":
    main()