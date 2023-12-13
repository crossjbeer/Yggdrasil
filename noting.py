import os 
import psycopg2 

import openai
openai.api_key = os.getenv('OPENAI_AUTH')

from chatter import Chatter 
from tokenizer import Tokenizer 
from colorcodes import Colorcodes

from parsers import make_parser_gpt_sql

from pg_embed import grab_k    

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


def main():
    parser = make_parser_gpt_sql()
    args = parser.parse_args() 

    tizer = Tokenizer(args.model)
    chatter = Chatter(args.model)
    color = Colorcodes()
    
    gpta = [] 
    gpta.append(chatter.getSysMsg(LORE_MASTER))

    prompt = args.query
    if(not prompt or not len(prompt)):
        prompt = chatter.usrprompt()

    print(color.pbold(f'~~ Chatting with {args.model} ~~'))
    while True:
        gptb = [chatter.getSysMsg(IGOR)]

        if(prompt is None):
            prompt = chatter.usrprompt()

        print(color.pred("\tConverting query into Embedding..."))
        response = openai.Embedding.create(
            input=prompt,
            model=args.embedder
        )
        embedding = response['data'][0]['embedding']

        print(color.pred(f'\tGrabbing {args.nvector} Associated Note Vectors'))
        vec = grab_k(embedding, k=args.nvector, **vars(args))

        content_list = vec['content']
        name_list    = vec['note']
        for ccont, cname in zip(content_list, name_list):
            msg = f"""NOTE: {cname}\n\n```{ccont}```"""
            gptb.append(chatter.getUsrMsg(msg))
        gptb.append(chatter.getUsrMsg('USER QUERY: {}'.format(prompt)))

        print(color.pbold(color.pred('\tSummarizing with IGOR...')))
        gptb_reply = chatter.passMessagesGetReply(gptb)

        gpta_msg = f"""IGOR SUMMARY: {gptb_reply}\n\nUSER QUERY: {prompt}"""
        gpta.append(chatter.getUsrMsg(gpta_msg))

        print(color.pbold(color.pred('\tPassing to LORE MASTER...')))
        reply = chatter.passMessagesGetReply(gpta)

        gpta.append(chatter.getAssMsg(reply))

        chatter.printMessages(gpta)

        input('Continue?')

        prompt = None 

        



if __name__ == "__main__":
    main()