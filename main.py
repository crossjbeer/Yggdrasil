import numpy as np 
import re
from collections import OrderedDict
import argparse

from chatter import Chatter 
from colorcodes import Colorcodes

from pg_vector import grab_k
from pg_embed import embed 
from pg_chat import new_chat, append_message, connect
from parsers import parser_gpt, parser_sql 


LORE_MASTER = """You are the LORE MASTER.
You preside over a cherished campaign of Dungeons and Dragons (DND).
Your job is to be the ultimate dnd assistant.

You have an assistant, IGOR.
IGOR will research for you, and provide you with summaries of relevant information they find. 
Please use IGOR's summaries to inform your answers. 

You will see messages with the following structure: 

** STRUCTURE **
IGOR SUMMARY: 
<igor's summary>

Knowledge Source: <source of knowledge> 
Source Description: <description of knowledge source> 

USER QUERY: <user query>
** STRUCTURE END **

Please use IGOR's summary to accurately answer the USER's query!
Be thorough and give the user the specific detail they are interested in.   
And most importantly, be creative and have fun!"""

IGOR = """You are a world-class researcher. 
Your job is to summarize information relevant to a given USER QUERY.

You will be presented with a block of INFORMATION.
This is a some chunk of information that may be relevant to the USER QUERY. 

The information may be accompanied by some metadata.
- DOCUMENT NAME: The name of the document storing the information. 
- KNOWLEDGE SOURCE: The name of the category of information the document belongs to. 
- SOURCE DESCRIPTION: A description of the knowledge source.

Read through the INFORMATION and included metadata. Summarize any information relevant to the USER QUERY. 

Below is an example of the structure you can expect: 

** STRUCTURE **
INFORMATION: 
```<information>```
METADATA: 
- DOCUMENT NAME: <document name>
- KNOWLEDGE SOURCE: <knowledge source>
- SOURCE DESCRIPTION: <source description>

USER QUERY: <question>
** STRUCTURE END ** 

DO NOT edit the information. 
DO NOT editoralize and add your own opinions and infomration. 
Try to maintain the original context of the information.
REMEMBER you are a RESEARCHER, not a writer.
REMEMBER to RESEARCH, not WRITE about what you find.  
Please write your summarized notes as a bulleted list. 
"""

TOKENMASTER = """You are the TOOL MASTER.
Your job is to help gather information. 
Specifically, you gather information to help the GAME MASTER (GM) of a Dungeons and Dragons (DND) Campaign.

You will be presented with THREE things: 
1) A USER QUERY: Some question or prompt related to DND, the campaign being run, or rules in general. 
2) A list of TOOLS: Sources of information that can be queried for information related to the USER QUERY. 
-- Note that some sources are more useful than others for specific queries. 
3) A set of TOKENS: These are your currency. You must spend these tokens to query the TOOLS. One query = one token. 

Please assign tokens to the TOOLS. The number of tokens assigned represents the amount of queries to be made. 
More tokens = more queries = more information from that tool. 

Please return your answer as a BULLETED LIST. 
See the example below: 

RESPONSE EXAMPLE: 
- tool 1: 3
- tool 2: 1
- tool 3: 0
- tool 4: 1

Now please go about your job. 
"""

QUERY_MASTER = """You are the QUERY MASTER.
Your job is to improve queries. 
A query is considered 'improved' when it contains more appropriate contextual information. 
But what does this mean? 

Your improved queries will help an Information Retrieval System (IRS). 
This IRS depends on conetextual information that the user may not provide in their query alone.

As an initial query, the user asks "What is the name of the dragon in the cave?".
The IRS returns that the dragon in the cave is named 'Smaug'.

Next, the user asks: "And what does he like to eat?"
This lacks sufficient context for the IRS.
The system will not know who 'he' is.
So the question would be better phrased as "What does Smaug like to eat?". 

Please also present several iterations of the question in your response.
This will give the IRS more opportunities to find the correct information.

Other example improvements to "And what does he like to eat?" include: 
1) "What does the dragon in the cave, Smaug, like to eat?"
2) "What sorts of foods does Smaug eat?"

You will be presented with a list of USER QUERIES, and a NEW QUERY. 
Please return the NEW QUERY and NOTHING ELSE.

Now please take a seat, get a sip of coffee, take a deep breath, and get ready to improve some queries!
You are a valuable member of our team and I look forward to seeing what you can do.
"""


TOOLS = {'notes':'Notes written by the GAME MASTER (GM) of a dnd campaign. Useful for specific world information, NPCs, lore, etc. Not useful for rules. This should likely be referenced in most cases.', 
         'players_handbook':'All information one must know to be a Dungeon and Dragons PLAYER. Includes rules for building characters, designing backgrounds, combat, spells, etc.', 
         'dungeon_masters_guide':'All information required to be a Dungeons and Dragons GAME MASTER (GM). Contains rules for building encounters, designing campaigns, etc.',
         'build_a_character': 'A small white-page sheet containing 10 steps on how to build a character.'
         }


def make_parser():
    parser = argparse.ArgumentParser(description="Chat with Yggy")

    parser = parser_gpt(parser)
    parser = parser_sql(parser)

    return(parser)

def sortXbyY(X, Y):
    return([x for _, x in sorted(zip(Y, X))])

def organize_information_from_vectors(vectors, knowledge_source=None, knowledge_source_description=None):
    all_docs = vectors['note']
    unique_docs = np.unique(all_docs)

    docs = {}
    for doc in unique_docs:
        content = [] 
        starting_lines = [] 

        for i in range(len(all_docs)):
            if(vectors['note'][i] == doc):
                content.append(vectors['content'][i])
                starting_lines.append(vectors['start_line'][i])

        content = sortXbyY(content, starting_lines)
        content = "".join(content)

        msg = f"INFORMATION:\n```\n{content}\n```\n"
        msg += f"METADATA:\n"
        msg += f"- DOCUMENT NAME: {doc}\n"
        if(knowledge_source):
            msg += f"- KNOWLEDGE SOURCE: {knowledge_source}\n"
            if(knowledge_source_description):
                msg += f"- SOURCE DESCRIPTION: {knowledge_source_description}\n"

        docs[doc] = msg

    return(docs)

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

        msg = f"NOTE: {note}\n"
        msg += f"```\n{content}\n```"

        notes[note] = msg

    for note in notes: 
        print(notes[note])
        print() 
    input()

    return(notes)

def parse_bulleted_list(text):
    # Remove any leading or trailing whitespace
    text = text.strip()

    # Find the bullet points using regular expressions
    bullet_pattern = r'(\*|\-|\+|\d+\.)\s+(.*)'
    bullet_matches = re.findall(bullet_pattern, text)

    # Extract the bullet points and return as a list
    bullet_list = [match[1] for match in bullet_matches]

    return bullet_list

def info_grab(prompt, nvec, embedder, namespace=None, *args, **kwargs):
    embedding = embed(prompt, embedder) 
    vec = grab_k(embedding, k=nvec, namespace=namespace, *args, **kwargs)

    return(vec)


def ask_querymaster(prompt, previous_prompts, chatter, querymaster_prompt=QUERY_MASTER, verbose=False, connection=None):
    color = Colorcodes()
    qm_msg = [chatter.getSysMsg(querymaster_prompt)]

    msg = f"PREVIOUS PROMPTS:\n"
    for i, prompt in enumerate(previous_prompts):
        msg += f"{i+1}) {prompt}\n"
    qm_msg.append(chatter.getUsrMsg(msg))

    msg = f'USER QUERY: {prompt}'
    qm_msg.append(chatter.getUsrMsg(msg))

    if(verbose):
        print(color.pbold(color.pred('\tPassing to QUERY MASTER...')))

    qm_reply = chatter.passMessagesGetReply(qm_msg)

    chat_id = None 
    if(connection):
        chat_id = new_chat(connection, prompt, 'querymaster')
        for msg in qm_msg: 
            append_message(connection, chat_id, msg['content'], msg['role'])
        append_message(connection, chat_id, qm_reply, 'assistant')

    return(qm_reply, chat_id)

def ask_tokenmaster(user_query, chatter, tools, tokens, toolmaster=TOKENMASTER, verbose=False, connection=None):
    color = Colorcodes()
    tm_msg = [chatter.getSysMsg(toolmaster)]

    msg = f'USER QUERY: {user_query}'
    msg += '\nTOOLS:'
    for tool in tools:
        msg += f'\n\t{tool}: {tools[tool]}'

    msg += f'\nTOKENS: {tokens}'
    tm_msg.append(chatter.getUsrMsg(msg))

    if(verbose):
        print(color.pbold(color.pred('\tPassing to Token Master...')))

    tm_reply_preparse = chatter.passMessagesGetReply(tm_msg)
    tm_reply = parse_bulleted_list(tm_reply_preparse)
    if(len(tm_reply)):
        try: 
            tm_reply = {tool.strip(): int(tok.strip()) for tool, tok in [reply.split(':') for reply in tm_reply]}
        except: 
            tm_reply = {'notes': tokens}
    else:
        tm_reply = {'notes': tokens}
    
    chat_id = None 
    if(connection):
        chat_id = new_chat(connection, user_query, 'tokenmaster')
        for msg in tm_msg: 
            append_message(connection, chat_id, msg['content'], msg['role'])
        append_message(connection, chat_id, tm_reply_preparse, 'assistant')

    return(tm_reply, chat_id)

def ask_igor(prompt, igor_notes, chatter, igor_prompt=IGOR, verbose=False, connection=None, *args, **kwargs):

    igor_msg = [chatter.getSysMsg(igor_prompt)] if igor_prompt else [] 

    for note in igor_notes:
        igor_msg.append(chatter.getUsrMsg(igor_notes[note]))

    igor_msg.append(chatter.getUsrMsg('USER QUERY: {}'.format(prompt)))

    igor_reply = chatter.passMessagesGetReply(igor_msg)

    chat_id = None 
    if(connection):
        chat_id = new_chat(connection, prompt, 'igor')
        for msg in igor_msg: 
            append_message(connection, chat_id, msg['content'], msg['role'])
        append_message(connection, chat_id, igor_reply, 'assistant')

    return(igor_reply, chat_id)

def ask_loremaster(prompt, igor_reply, chatter, messages=[], loremaster_prompt = LORE_MASTER, verbose=False, connection=None):
    if(not len(messages)):
        messages.append(chatter.getUsrMsg(loremaster_prompt))

    loremaster_msg = f"""IGOR SUMMARY:\n{igor_reply}\n\nUSER QUERY: {prompt}"""
    messages.append(chatter.getUsrMsg(loremaster_msg))

    if verbose:
        color = Colorcodes()
        print(color.pbold(color.pred('\tPassing to LORE MASTER...')))

    reply = chatter.passMessagesGetReply(messages)

    if(connection):
        chat_id = new_chat(connection, prompt, 'loremaster')
        for msg in messages: 
            append_message(connection, chat_id, msg['content'], msg['role'])
        append_message(connection, chat_id, reply, 'assistant')

    return(reply, messages, chat_id)


def yggy_step(prompt, chatter, embedder, previous_prompts=[], verbose=False, total_tokens = 5, tokenmaster=TOKENMASTER, igor=IGOR, loremaster=LORE_MASTER, tools=TOOLS, loremaster_dialogue=[], connection=None, *args, **kwargs):
    associated_ids = [] 
    
    color = Colorcodes() 
    igor_summaries = OrderedDict() 

    if(len(previous_prompts)):
        previous_prompts.append(prompt)
        prompt, associated_id = ask_querymaster(prompt, previous_prompts, chatter, querymaster_prompt=QUERY_MASTER, verbose=verbose, connection=connection)
        associated_ids.append(associated_id)
    else:
        previous_prompts.append(prompt)

    tm_reply, tm_id = ask_tokenmaster(prompt, chatter, tools, total_tokens, verbose=verbose, toolmaster=tokenmaster, connection=connection)
    associated_ids.append(tm_id)

    sorted_keys = sorted(tm_reply, key=lambda x: tm_reply[x], reverse=True)
    for i, sortkey in enumerate(sorted_keys):
        if(tm_reply[sortkey] == 0):
            continue

        print(color.pgreen(f"\t\tTool {i+1}: {sortkey} [{tm_reply[sortkey]} Tokens]"))

    for i, sortkey in enumerate(sorted_keys):
        if(tm_reply[sortkey] == 0):
            continue

        note_vector = info_grab(prompt, tm_reply[sortkey], embedder, namespace=sortkey, *args, **kwargs)
        igor_info = organize_information_from_vectors(note_vector, knowledge_source=sortkey, knowledge_source_description=tools[sortkey])

        if(verbose):
            print(color.pred(f"\t\tSummarizing {sortkey} with IGOR..."))

        igor_summary, igor_id = ask_igor(prompt, igor_info, chatter, igor, verbose=verbose, connection=connection)
        igor_summaries[sortkey] = igor_summary
        associated_ids.append(igor_id)

    full_igor_summary = ""
    for note in igor_summaries: 
        full_igor_summary += f"Knowledge Source: {note}\nSource Description: {tools[note]}\n\nIgor Summary:\n{igor_summaries[note]}\n\n"

    loremaster_reply, loremaster_msg, lm_id = ask_loremaster(prompt, full_igor_summary, chatter, messages=loremaster_dialogue, verbose=verbose, loremaster_prompt=loremaster, connection=connection)
    associated_ids.append(lm_id)

    return(loremaster_reply, loremaster_msg, associated_ids, previous_prompts)

def yggy(model, query, nvector, embedder, loremaster=LORE_MASTER, igor=IGOR, toolmaster=TOKENMASTER, verbose=True, connection=None, *args, **kwargs):
    color = Colorcodes()
    chatter = Chatter(model)

    prompt = query 
    previous_prompts = [] 
    chat_id = None
    loremaster_dialogue = [chatter.getSysMsg(loremaster)] 

    if(verbose):
        print(color.pbold(f'~~ Chatting with {model} ~~'))

    while True:
        associated_ids = []

        if(prompt is None):
            prompt = chatter.usrprompt()

        if(connection and not chat_id):
            # There is a connection and no chat id has been set, so we are working with a new chat. Generate the id 
            chat_id = new_chat(connection, prompt, 'yggy')

        if(chat_id):
            # Pass the message to the high-level abstraction chat, yggy
            append_message(connection, chat_id, prompt, 'user')

        loremaster_reply, _, step_ids, previous_prompts = yggy_step(prompt, chatter, embedder, previous_prompts=previous_prompts, verbose=verbose, total_tokens=nvector, toolmaster=toolmaster, igor=igor, loremaster=loremaster, loremaster_dialogue=loremaster_dialogue, connection=connection, chat_id=chat_id, *args, **kwargs)
        loremaster_dialogue.append(chatter.getAssMsg(loremaster_reply))
        associated_ids += step_ids

        print(color.pgreen(loremaster_reply))
        if(connection and chat_id):
            append_message(connection, chat_id, loremaster_reply, 'assistant', associated_ids=associated_ids)

        input('Continue?')

        prompt = None

def yggy_print():
    color = Colorcodes()

    s = """                   _,---.       _,---.                
 ,--.-.  .-,--._.='.'-,  \  _.='.'-,  \,--.-.  .-,--. 
/==/- / /=/_ //==.'-     / /==.'-     /==/- / /=/_ /  
\==\, \/=/. //==/ -   .-' /==/ -   .-'\==\, \/=/. /   
 \==\  \/ -/ |==|_   /_,-.|==|_   /_,-.\==\  \/ -/    
  |==|  ,_/  |==|  , \_.' )==|  , \_.' )|==|  ,_/     
  \==\-, /   \==\-  ,    (\==\-  ,    ( \==\-, /      
  /==/._/     /==/ _  ,  / /==/ _  ,  / /==/._/       
  `--`-`      `--`------'  `--`------'  `--`-`        
"""

    print("\n"*10)
    print(color.porange(s))

    return() 


def main():
    parser = make_parser()
    args = parser.parse_args() 

    yggy_print()

    connection = None 
    if('host' in args):
        connection = connect(**vars(args))

    yggy(**vars(args), connection=connection)

        



if __name__ == "__main__":
    main()