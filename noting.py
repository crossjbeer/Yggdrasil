import numpy as np 
import re
from collections import OrderedDict
import argparse

from chatter import Chatter 
from colorcodes import Colorcodes

#from parsers import make_parser_gpt_sql
from pg_vector import grab_k
from pg_embed import embed 
from pg_chat import start_chat, connect
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

IGOR = """ 
You are a world-class researcher. 
Your job is to summarize relevant information. 

You will be presented with a USER QUERY and a set of NOTES.
Read through the notes and summarize any information relevant to the USER QUERY. 

You can expect to see the name of the note, followed by any information from that note. 
Information is passed with the following structure: 

USER QUERY: <question>

NOTE: <Note Name>
```
Information from <Note Name>...
```

Please write your summarized notes as a bulleted list. 
"""

IGOR_ADDED_CONTEXT = """You are a world-class researcher. 
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

TOOLMASTER = """You are the TOOL MASTER.
Your job is to help the GAME MASTER (GM) of a Dungeons and Dragons Campaign by selecting the best tool for the job.

You will be presented with a USER QUERY. This is some question or prompt related to the campaign. 
You will be presented with a list of TOOLS. Each TOOL represents a source of knowledge. The tools may have accompanying information, to add context.

Most USER QUERYs can be answered using only the NOTES. These are written by the GM and contain information about the world, the characters, NPC's, campaign, etc. 
However, there will be times when other information is necessary. These are situations where the GM is interested in rules, roll tables, and niche facts of the game. 

Please rank the tools presented, in order of usefulness. 
Return your answer as a BULLETED LIST. 

Example Output: 
- notes
- players handbook
- dungeon masters guide 
"""

TOOLMASTER_TOKEN = """You are the TOOL MASTER.
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

ORCHESTRATOR = """You are the ORCHESTRATOR. 
You must determine if a question has been adequately answered. 

You will see a USER QUERY. This is some question or prompt related to a dnd campaign.
You will also see an ANSWER. This is some answer to the USER QUERY. 
Some history may also be included, for added context.
A list of TOOLS used to answer the USER QUERY may also be included.

Reading through the ANSWER, and all available context, please determine if the USER QUERY has been adequately answered.
If the ANSWER adequately answers the USER QUERY, please write 'adequate'.  

Otherwise, if you find the question has not been adequately answered, please return ANY AND ALL criticism as a BULLETED LIST.
"""

QUERY_MASTER = """You are the QUERY MASTER. 
You will be provided with a USER QUERY.
The USER QUERY will be turned into a vector embedding, and used to search.

Please augment the USER QUERY by adding any information you think will help the vector embedding.
This includes: 
- alternative forms of asking the question
- adding more descriptive words to the question
- adding appropriate context 

Below are your requirements: 
- Return the IMPROVED QUERY and NOTHING ELSE. 
- DO NOT editoralize the USER QUERY. 
- DO NOT imagine information that isn't explicitly stated. 
- DO NOT add your own opinions.
- DO NOT assume. 
"""

TOOLS = {'notes':'Notes written by the GAME MASTER (GM) of a dnd campaign. Useful for specific world information, NPCs, lore, etc. Not useful for rules. This should likely be referenced in most cases.', 
         'players handbook':'All information one must know to be a Dungeon and Dragons PLAYER. Includes rules for building characters, designing backgrounds, combat, spells, etc.', 
         'dungeon masters guide':'All information required to be a Dungeons and Dragons GAME MASTER (GM). Contains rules for building encounters, designing campaigns, etc.',
         'build a character': 'A small white-page sheet containing 10 steps on how to build a character.'
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


def ask_querymaster(prompt, chatter, querymaster_prompt=QUERY_MASTER, verbose=False):
    color = Colorcodes()
    qm_msg = [chatter.getSysMsg(querymaster_prompt)]

    msg = f'USER QUERY: {prompt}'
    qm_msg.append(chatter.getUsrMsg(msg))

    if(verbose):
        print(color.pbold(color.pred('\tPassing to QUERY MASTER...')))

    qm_reply = chatter.passMessagesGetReply(qm_msg)

    return(qm_reply)

def ask_toolmaster(user_query, tm_chatter, tools, toolmaster_prompt=TOOLMASTER, verbose=False):
    color = Colorcodes()
    tm_msg = [tm_chatter.getSysMsg(toolmaster_prompt)]

    msg = f'USER QUERY: {user_query}'
    msg += '\nTOOLS:'
    for tool in tools:
        msg += f'\n\t{tool}: {tools[tool]}'

    tm_msg.append(tm_chatter.getUsrMsg(msg))

    if(verbose):
        print(color.pbold(color.pred('\tPassing to TOOL MASTER...')))

    #tm_chatter.printMessages(tm_msg)

    tm_reply = tm_chatter.passMessagesGetReply(tm_msg)
    tm_reply = parse_bulleted_list(tm_reply)

    return(tm_reply)


def ask_tokenmaster(user_query, chatter, tools, tokens, toolmaster=TOOLMASTER_TOKEN, verbose=False):
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
        #chatter.printMessages(tm_msg)   
        #input() 

    tm_reply = chatter.passMessagesGetReply(tm_msg)
    tm_reply = parse_bulleted_list(tm_reply)
    if(len(tm_reply)):
        try: 
            tm_reply = {tool.strip(): int(tok.strip()) for tool, tok in [reply.split(':') for reply in tm_reply]}
        except: 
            tm_reply = {'notes': tokens}
    else:
        tm_reply = {'notes': tokens}

    return(tm_reply)


def ask_igor(prompt, embedder='text-embedding-ada-002', model='gpt-3.5-turbo', nvector=5, host='localhost', port='', user='crossland', password='pass', database='yggdrasil', chatter=None, igor_prompt=IGOR, verbose=False, namespace=None):
    color = Colorcodes()
    igor_msg = [chatter.getSysMsg(igor_prompt)] if igor_prompt else [] 

    if(not chatter):
        chatter = Chatter(model)

    if(verbose):
        print(color.pred(f"\tConverting query into Embedding with model {embedder}..."))

    embedding = embed(prompt, embedder)

    if(verbose):
        print(color.pred(f'\tGrabbing {nvector} Associated Note Vectors'))

    vec = grab_k(embedding, k=nvector, host=host, port=port, user=user, password=password, database=database, namespace=namespace)

    igor_notes = organize_notes_from_vectors(vec)
    for note in igor_notes:
        igor_msg.append(chatter.getUsrMsg(igor_notes[note]))

    igor_msg.append(chatter.getUsrMsg('USER QUERY: {}'.format(prompt)))

    if(verbose):
        print(color.pbold(color.pred('\tSummarizing with IGOR...')))
    igor_reply = chatter.passMessagesGetReply(igor_msg)

    return(igor_reply)

def ask_igor_small(prompt, igor_notes, chatter=None, model='gpt-3.5-turbo', igor_prompt=IGOR, verbose=False):
    if(not chatter):
        chatter = Chatter(model)

    igor_msg = [chatter.getSysMsg(igor_prompt)] if igor_prompt else [] 

    for note in igor_notes:
        igor_msg.append(chatter.getUsrMsg(igor_notes[note]))

    igor_msg.append(chatter.getUsrMsg('USER QUERY: {}'.format(prompt)))

    if(verbose):
        color = Colorcodes()
        print(color.pbold(color.pred('\tSummarizing with IGOR...')))
        #chatter.printMessages(igor_msg)

    igor_reply = chatter.passMessagesGetReply(igor_msg)

    return(igor_reply)


def ask_loremaster(prompt, igor_reply, chatter, messages=[], loremaster_prompt = LORE_MASTER, verbose=False):
    if(not len(messages)):
        messages.append(chatter.getUsrMsg(loremaster_prompt))

    loremaster_msg = f"""IGOR SUMMARY:\n{igor_reply}\n\nUSER QUERY: {prompt}"""
    messages.append(chatter.getUsrMsg(loremaster_msg))

    if verbose:
        color = Colorcodes()
        print(color.pbold(color.pred('\tPassing to LORE MASTER...')))

    reply = chatter.passMessagesGetReply(messages)
    return(reply, messages)


def ask_orchestrator(prompt, answer, chatter, orchestrator_prompt=ORCHESTRATOR, previous_messages = [], used_tools = {}, remaining_tools = {}, verbose=False):
    orch_msg = [chatter.getSysMsg(orchestrator_prompt)] if orchestrator_prompt else [] 

    orch_msg.append(chatter.getUsrMsg('USER QUERY: {}'.format(prompt)))
    orch_msg.append(chatter.getUsrMsg('ANSWER: {}'.format(answer)))

    if(len(previous_messages)):
        orch_msg.append(chatter.getUsrMsg('PREVIOUS MESSAGES:'))
        for msg in previous_messages:
            orch_msg.append(msg)
        orch_msg.append(chatter.getUsrMsg('END PREVIOUS MESSAGES'))

    if(len(used_tools)):
        msg = 'USED TOOLS'
        for tool in used_tools:
            msg += f'\n\t{tool}: {used_tools[tool]}'

        orch_msg.append(chatter.getUsrMsg(msg))

    if(len(remaining_tools)):
        msg = 'REMAINING TOOLS'
        for tool in remaining_tools:
            msg += f'\n\t{tool}: {remaining_tools[tool]}'
        
        orch_msg.append(chatter.getUsrMsg(msg))

    orch_msg.append(chatter.getUsrMsg('Now please determine if the answer is adequate. If so, please write nothing. Otherwise, determine what should be improved.'))

    if(verbose):
        color = Colorcodes()
        print(color.pbold(color.pred('\tPassing to ORCHESTRATOR...')))

    orch_reply = chatter.passMessagesGetReply(orch_msg)

    return(orch_reply)


def noting(model, query, nvector, embedder, host, port, user, password, database, lore_master=LORE_MASTER, igor=IGOR, verbose=True, *args, **kwargs):
    color = Colorcodes()
    chat_id = None
    chatter = Chatter(model)

    print(color.pbold(f'~~ Chatting with {model} ~~'))

    try:
        connection = connect(host, port, user, password, database)
    except:
        connection = None 
        pass 

    if(connection):
        chat_id = start_chat(connection, lore_master, 'system', title=True, title_msg=query)

    loremaster_msg = [] 
    prompt = query
    while True:
        if(prompt is None):
            prompt = chatter.usrprompt()

        tm_reply = ask_toolmaster(prompt, chatter, TOOLS, verbose=verbose)
        print("Ranked Tools: ", tm_reply)

        top_tool = tm_reply[0].lower().strip()
        print(color.pred(f'Tool Master Selected [{top_tool}]'))
        if(top_tool == 'players handbook'):
            igor_reply = ask_igor(prompt, embedder, model, nvector*2, host, port, user, password, database, chatter, igor, verbose=verbose, namespace='players handbook')
        elif(top_tool == 'dungeon masters guide'):
            igor_reply = ask_igor(prompt, embedder, model, nvector*2, host, port, user, password, database, chatter, igor, verbose=verbose, namespace='dungeon masters guide')
        else:
            igor_reply = ask_igor(prompt, embedder, model, nvector, host, port, user, password, database, chatter, igor, verbose=verbose, namespace='note')

        loremaster_reply, loremaster_msg = ask_loremaster(prompt, igor_reply, chatter, messages=loremaster_msg, verbose=verbose, loremaster_prompt=lore_master)
        loremaster_msg.append(chatter.getAssMsg(loremaster_reply))

        #if(connection and chat_id):
        #    append_message(connection, chat_id, loremaster_msg[-2]['content'], 'user')
        #    append_message(connection, chat_id, loremaster_msg[-1]['content'], 'assistant')

        #chatter.printMessages(loremaster_msg[-2:])
        input('Continue?')

        prompt = None 

def orchestrate_step(prompt, model, chatter, nvector, embedder, verbose, toolmaster=TOOLMASTER, igor=IGOR, loremaster=LORE_MASTER, orchestrator=ORCHESTRATOR, tools=TOOLS, loremaster_dialogue=[], *args, **kwargs):
    color = Colorcodes() 
    remaining_tools = tools.copy()
    used_tools = OrderedDict()
    igor_summaries = OrderedDict()

    tm_reply = ask_toolmaster(prompt, chatter, TOOLS, verbose=verbose)
    print(color.pred(f'\tRanked Tools: {tm_reply}'))
    for ranked_tool in tm_reply: 
        ranked_tool = ranked_tool.lower().strip()

        if(ranked_tool not in tools):
            continue 

        namespace = ranked_tool 
        used_tools[ranked_tool] = tools[ranked_tool]
        remaining_tools.pop(ranked_tool)

        print(color.pred(f"Grabbing notes from {ranked_tool}..."))
        note_vector = info_grab(prompt, nvector, embedder, namespace=namespace, *args, **kwargs)
        igor_notes  = organize_notes_from_vectors(note_vector)

        igor_summary = ask_igor_small(prompt, igor_notes, chatter, model, igor, verbose=verbose)
        igor_summaries[ranked_tool] = igor_summary

        full_igor_summary = ""
        for note in igor_summaries: 
            full_igor_summary += f"Knowledge Source: {note}\n\nIgor Summary:\n{igor_summaries[note]}"

        loremaster_reply, _ = ask_loremaster(prompt, full_igor_summary, chatter, messages=loremaster_dialogue, verbose=verbose, loremaster_prompt=loremaster)

        orchestrator_reply = ask_orchestrator(prompt, loremaster_reply, chatter, verbose=verbose, used_tools=used_tools, remaining_tools=remaining_tools, previous_messages=loremaster_dialogue, orchestrator_prompt=orchestrator)
        orchestrator_reply = orchestrator_reply.lower().strip()

        print(orchestrator_reply)
        if('not adequate' in orchestrator_reply or 'not adequately' in orchestrator_reply):
            continue 

        if(not len(orchestrator_reply) or 'no changes' in orchestrator_reply or 'this answer is adequate.' in orchestrator_reply or 'the answer is adequate.' in orchestrator_reply or 'adequate' in orchestrator_reply):
            break 

    return(loremaster_reply)

def tokenmaster_step(prompt, model, chatter, embedder, verbose, total_tokens = 5, toolmaster=TOOLMASTER_TOKEN, igor=IGOR, loremaster=LORE_MASTER, tools=TOOLS, loremaster_dialogue=[], *args, **kwargs):
    color = Colorcodes() 
    igor_summaries = OrderedDict() 

    tm_reply = ask_tokenmaster(prompt, chatter, tools, total_tokens, verbose=verbose, toolmaster=toolmaster)

    sorted_keys = sorted(tm_reply, key=lambda x: tm_reply[x], reverse=True)
    for i, sortkey in enumerate(sorted_keys):
        if(tm_reply[sortkey] == 0):
            continue
        print(color.pgreen(f"\t\tTool {i+1}: {sortkey} [{tm_reply[sortkey]} Tokens]"))

    for i, sortkey in enumerate(sorted_keys):
        note_vector = info_grab(prompt, tm_reply[sortkey], embedder, namespace=sortkey, *args, **kwargs)
        #igor_notes = organize_notes_from_vectors(note_vector)
        igor_info = organize_information_from_vectors(note_vector, knowledge_source=sortkey, knowledge_source_description=tools[sortkey])

        igor_summary = ask_igor_small(prompt, igor_info, chatter, model, igor, verbose=verbose)
        igor_summaries[sortkey] = igor_summary

    full_igor_summary = ""
    for note in igor_summaries: 
        full_igor_summary += f"Knowledge Source: {note}\nSource Description: {tools[note]}\n\nIgor Summary:\n{igor_summaries[note]}\n\n"

    print("Full Igor Summary:\n", full_igor_summary)

    loremaster_reply, loremaster_msg = ask_loremaster(prompt, full_igor_summary, chatter, messages=loremaster_dialogue, verbose=verbose, loremaster_prompt=loremaster)

    return(loremaster_reply, loremaster_msg)

def orchestrate(model, query, nvector, embedder, lore_master=LORE_MASTER, igor=IGOR, verbose=True, *args, **kwargs):
    color = Colorcodes()
    chatter = Chatter(model)

    print(color.pbold(f'~~ Chatting with {model} ~~'))

    loremaster_dialogue = [] 
    loremaster_dialogue.append(chatter.getSysMsg(lore_master))
    prompt = query 

    while True:
        if(prompt is None):
            prompt = chatter.usrprompt()

        loremaster_reply = orchestrate_step(prompt, model, chatter, nvector, embedder, verbose, toolmaster=TOOLMASTER, igor=igor, loremaster=lore_master, orchestrator=ORCHESTRATOR, *args, **kwargs)
        loremaster_dialogue.append(chatter.getAssMsg(loremaster_reply))

        print(color.pgreen(loremaster_reply))
        input('Continue?')

        prompt = None 

def tokenmaster(model, query, nvector, embedder, loremaster=LORE_MASTER, igor=IGOR_ADDED_CONTEXT, toolmaster=TOOLMASTER_TOKEN, verbose=True, *args, **kwargs):
    """
    Here we will simplify the orchestration endpoint. Right now the orchestrator works after the Igor+Lore Master step. 
    The Tool Master first ranks the tools it hopes to use. 
    Then, the tools are looped over. 
    For each tool, we query information, ask Igor to summarize relevant information, and pass that to the Lore Master to maintain our dialogue. 
    Then, finally, the Orchestrator discerns if the given answer is adequate. 
    If so, the answer is returned. Otherwise, we pass another tool's worth of info to Igor and then pass all the Igor Summaries to Lore master to generate another response. 
    
    I would like to change this structure. We are going to retool the toolmaster to change his functionality. 
    We are going to give the Tool Master Tokens to spend. They will use these tokens to pull information from tools. 

    Then, we will give all the information gathered to one or more Igor's to summarize. Once this is done, we pass to Lore Master and get whatever we get. 
    We eliminate the Orchestration Step alltogether.  
    """

    color = Colorcodes()
    chatter = Chatter(model)

    print(color.pbold(f'~~ Chatting with {model} ~~'))

    loremaster_dialogue = [] 
    loremaster_dialogue.append(chatter.getSysMsg(loremaster))

    prompt = query 
    while True:
        if(prompt is None):
            prompt = chatter.usrprompt()

        qm_reply = ask_querymaster(prompt, chatter, querymaster_prompt=QUERY_MASTER, verbose=verbose)
        print(qm_reply)
        prompt = qm_reply 

        loremaster_reply, _ = tokenmaster_step(prompt, model, chatter, embedder, verbose, total_tokens=nvector, toolmaster=toolmaster, igor=igor, loremaster=loremaster, loremaster_dialogue=loremaster_dialogue, *args, **kwargs)
        loremaster_dialogue.append(chatter.getAssMsg(loremaster_reply))

        print(color.pgreen(loremaster_reply))
        input('Continue?')

        prompt = None

    return() 



def main():
    parser = make_parser()
    args = parser.parse_args() 

    #noting(**vars(args))
    #orchestrate(**vars(args))
    tokenmaster(**vars(args))

        



if __name__ == "__main__":
    main()