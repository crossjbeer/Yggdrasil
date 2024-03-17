import argparse 

from parsers import parser_gpt, parser_sql, parser_doc
from chatter import Chatter 
from scripter import Scripter 
import re

GRAPHER = """You are the GRAPHER. 
You are back to another day of work as the foremost expert in building knowledge graphs, which you have done for some time and enjoy thoroughly. 
Your job is to build entries to a KNOWLEDGE GRAPH from a SNIPPET of text. 

As you already know, a knowledge graph is defined as a set of nodes and edges.
Each node is an entity {person, place, thing, idea} and each edge is a relationship between two entities. 
A knowledge graph therefore abstracts relationships between entities and is very useful for building a model of the world.

We can build knowledge graphs from anything we can read, just by breaking them down simply. 
Take the following example: 

SNIPPET: 
'John went to the store.' 

Here, we see two entities:
1) John
2) Store

We see one relationship: 
1) went to

We can build an entry to our KNOWLEDGE GRAPH as follows: 
1) First, we convert the relationship to a 'relationship type'
went to -> WENT_TO 
2) Then, we present the information in <subject> | <relationship> | <object> format.
John | WENT_TO | Store 

Here we have done the following: 
1) Numbered the entries 
2) separated the posts with a (|) character.
3) Presented the information in <subject> | <relationship> | <object> format.
4) Converted the relationship from text to a 'relationship type'. i.e. 'has' -> HAS, 'went to' -> WENT_TO, 'is' -> IS, etc.

Please keep your relationship types simple and use underscores instead of spaces. 
Remember to be accurate in your entries. They should accurately represent the relationships between entities. 
Be creative in identifying relationships and entities. Be sure to capture as many entities and relationships as possible. 

Now, let's get started!
When you see a new SNIPPET, identify the entities, then all the relationships. 
Write the entities as a bulleted list, followed by the relationships as a bulleted list. 
Finally, using what you gathered, build the entries to the KNOWLEDGE GRAPH as a numbered list with the format <subject> | <relationship> | <object>. 
Be sure to refer back to the SNIPPET to check your work.

Please take a seat, get a sip of your coffee, take a deep breath, and get ready to build some knowledge graphs!
You are a valuable member of our team and I look forward to seeing what you can do. 
"""

RECONCILER = """You are the RECONCILER.
Your job is to reconcile the knowledge graph entries several GRAPHERS have built. 

As you already know, a knowledge graph is defined as a set of nodes and edges.
Each node is an entity {person, place, thing, idea} and each edge is a relationship between two entities. 
A knowledge graph therefore abstracts relationships between entities and is very useful for building a model of the world.
We can build knowledge graphs from anything we can read, just by breaking them down simply. 

We have several GRAPHERs, each of which have observed the SAME snippet of text, and built their own entries for a KNOWLEDGE GRAPH. 
Your job is to reconcile the entries from each GRAPHER into a single set of entries. 
There will likely be plenty of overlap. See if any entries are slightly similar and join them if so. 
If there are any entries that are not similar, add them to the list.

You will see each GRAPHER's entries as a numbered list, presented as such: 
GRAPHER 1: 
1) <subject> | <relationship> | <object>
2) <subject> | <relationship> | <object>
...
N) <subject> | <relationship> | <object>

GRAPHER 2:
1) <subject> | <relationship> | <object> 
... 

GRAPHER N: ...


Your output should be a numbered list of knowledge graph entries, presented as such:
1) <subject> | <relationship> | <object>
2) <subject> | <relationship> | <object>
...
N) <subject> | <relationship> | <object>

Now please take a seat, get a sip of coffee, take a deep breath, and get ready to reconcile some knowledge graphs!
You are a valuable member of our team and I look forward to seeing what you can do.
"""

def make_parser():
    parser = argparse.ArgumentParser(description='Build corpus of graph entries.')

    parser.add_argument('--grapher_repetitions', type=int, default=1, help='Number of times to repeat the grapher prompt.')

    parser = parser_doc(parser)
    parser = parser_gpt(parser)
    parser = parser_sql(parser) 

    return(parser)

def parse_numbered_list(text):
    lines = text.split('\n')
    numbered_list = []

    for line in lines:
        match = re.match(r'^(\d+)\)', line)
        if match:
            number = int(match.group(1))
            content = line[match.end():].strip()
            numbered_list.append((number, content))

    return numbered_list


def ask_grapher(snippet, chatter, grapher_prompt = GRAPHER):
    messages = [] 

    messages.append(chatter.getSysMsg(grapher_prompt))
    messages.append(chatter.getSysMsg(snippet))

    #chatter.printMessages(messages)
    #input()

    reply = chatter(messages)
    #print(reply)
    #input()

    reply_parse = parse_numbered_list(reply)

    return(reply_parse)

def ask_reconciler(grapher_entries, chatter, reconciler_prompt = RECONCILER):
    messages = [] 

    messages.append(chatter.getSysMsg(reconciler_prompt))
    #messages.append(chatter.getSysMsg(grapher_entries))

    for i, entry in enumerate(grapher_entries):
        messages.append(chatter.getUsrMsg(f"GRAPHER {i+1}:\n{entry}"))

    #chatter.printMessages(messages)
    #input()

    reply = chatter(messages)
    #print(reply)
    #input()

    reply_parse = parse_numbered_list(reply)

    return(reply_parse)

def parse_grapher_reply(entry):
    try:
        sub, rel, obj = entry.split('|')
        sub = sub.strip().lower()
        rel = rel.strip()
        obj = obj.strip().lower()

        sub = sub.replace(' ', '_')
        obj = obj.replace(' ', '_')
    except:
        print("PROBLEM ENTRY: ", entry)
        return(None, None, None)

    return(sub, rel, obj)

def main():
    """
    Pass a path, get a knowledge graph? Maybe! 
    """

    parser = make_parser()
    args = parser.parse_args()

    chatter = Chatter(args.model)
    scripter = Scripter()   
    df = scripter.loadTxt(args.path, parseOnSentence=True)

    import pandas as pd 
    graph = pd.DataFrame(columns=['subject', 'relationship', 'object'])

    chunks = scripter.tokenChunks(df, args.token_lim)
    for i, chunk in enumerate(chunks):
        # Loop over the text chunks, building a series of graph entries each time. 
        if(i % 100 == 0):
            print('Continue?')

        print(f"$ Chunk {i} of {len(chunks)}")

        grapher_replies = []
        for j in range(args.grapher_repetitions):
            # Ask the grapher to build the entries.
            reply = ask_grapher(chunk, chatter)

            grapher_replies.append(reply)

        if(len(grapher_replies)  > 1):
            # Ask the reconciler to reconcile the entries.
            reply = ask_reconciler(grapher_replies, chatter)
        else:
            reply = grapher_replies[0]

        for num, entry in reply:
            sub, rel, obj = parse_grapher_reply(entry)
            if(sub is None):
                continue 

            #graph = graph.append({'subject': sub, 'relationship': rel, 'object': obj}, ignore_index=True)
            graph.loc[len(graph)] = [sub, rel, obj]

            print(f"{num}. {sub} | {rel} | {obj}")

        graph.to_csv('graph.csv', index=False)

        #input()

if(__name__ == '__main__'):
    main()