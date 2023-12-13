import openai
import os 
import argparse 
import pinecone 
import numpy as np 

from chatter import Colorcodes, Chatter
from scripter import Scripter

openai.api_key = os.getenv('OPENAI_AUTH')

# Alternatively just set your own api key (just don't upload to git!)
pinecone.init(api_key = os.getenv('PINECONE_AUTH'), environment='asia-southeast1-gcp-free')

INDEX = pinecone.Index('yggy')
COLORCODE = Colorcodes() 

from tokenizer import Tokenizer

def make_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-q', '--query', help='Query for Chat GPT', type=str, default=None, required=False)
    parser.add_argument('-m', '--model', help='Open AI model to use [gpt3.5-turbo, gpt4]', type=str, default='gpt-4')
    parser.add_argument('-n', '--nvector', help='Number of vectors to query', type=int, default=5)
    parser.add_argument('--host', help='Database host', type=str, default='localhost')
    parser.add_argument('--user', help='Database user', type=str, default='ygg')
    parser.add_argument('--db', help='Database name', type=str, default='yggdrasil')
    parser.add_argument('--password', help='Database password', type=str, default=None)
    parser.add_argument('--table', help='Table with Transcriptions', default='transcript', type=str)
    parser.add_argument('--stopwords', help='Eliminate stopwords from transcript', action='store_true')

    return(parser)


def main():
    messages = [{'role':'system', 'content':"""You are the Lore Master. You preside over the sacred DM notes of a Dungeons and Dragons Campaign.
        A group of friends spend time and laugh together because of this, and it is of great importance. 
        Your job is to be the ultimate dnd assistant.
        To help in your job, you are given chunks of notes relevant to your campaign. Use these notes to answer the user's question to the best of your ability. 
        Remember, these notes are sacred and should be adheared to. 
        Be thorough and give the user the specific detail they are interested in. 
        
        Here are the speaker codes and characters / roles:
        <1> DM
        <2> Likkvorn
        <3> Russet Crow
        <4> Lief
        <5> Oskar
        """}]

    parser = make_parser()
    args = parser.parse_args() 

    tizer = Tokenizer(args.model)

    script = Scripter()

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
        include_values=True, 
        namespace='notes'
    )
    print(f"{COLORCODE.orange}Pinecone Query Complete{COLORCODE.reset}\n")

    relatedID = [i['id'] for i in relatedVectors['matches']]
    filename = []
    id = [] 
    batchsize = [] 
    for rid in relatedID:
        fn, details = rid.split(']')
        fn = fn[1:]

        _, sid, bs = details.split('_')

        filename.append(fn)
        id.append(int(sid))
        batchsize.append(int(bs))

    unique_notes = np.unique(filename)
    noteToInterval = {}
    
    for s in unique_notes:
        indices = [id[i] for i in range(len(id)) if filename[i] == s]
        bs      = [batchsize[i] for i in range(len(id)) if filename[i] == s]

        intervals = [(id[i], id[i] + batchsize[i]) for i in range(len(indices))]
        intervals.sort(key=lambda x: x[0])

        if(len(intervals) == 1):
            interval = intervals[0]
            noteToInterval[s] = [interval]
            continue

        merged_intervals = [intervals[0]]
        for interval in intervals[1:]:
            prev_start, prev_end = merged_intervals[-1]
            curr_start, curr_end = interval

            # If the current interval overlaps with the previous one, merge them
            if curr_start <= prev_end:
                merged_intervals[-1] = (prev_start, max(prev_end, curr_end))
            else:
                # If the current interval doesn't overlap, add it to the list
                merged_intervals.append(interval)

        noteToInterval[s] = merged_intervals

    allText = ""
    overall_tokens = 0 
    for note in noteToInterval:
        print("Loading note: [{}]".format(note))
        allText += "***\n{}\n***\n".format(note)

        c_script = Scripter()
        c_df = c_script.loadTxt('./notes/{}.txt'.format(note))

        all_tokens = 0 
        for start, end in noteToInterval[note]:
            c_str = c_script.getStrRows(c_df, start, end-start)
            allText += "\n".join(c_str) + "\n"

            tokens = tizer.calculate_tokens("\n".join(c_str))
            all_tokens += tokens 
            print("  - Lines {} -> {} ({} Tokens)".format(start, end, tokens))
        print("[{}] Tokens: {}".format(note, all_tokens))
        overall_tokens += all_tokens

    print("All tokens added: {}".format(overall_tokens))


    allText += """Above you see snippets from various notes related to this campaign.
Each new note is predicated by:
***
<Note Name>
***

Please Use this information as context for the user query\n\n. 
"""

    messages = [
            {'role':'user', 'content':'Context:'},
            {'role':'user', 'content':allText},
            {'role':'user', 'content':'User Query:'}
        ]
    
    chat = Chatter(args.model)

    chat.chat_db(prompt, True, messages)
    

if (__name__ == "__main__"):
    main()
