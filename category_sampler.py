"""
I want to give this a .txt.
We will chunk this up according to a 'token_lim'
We will randomly sample n chunks. 
We will pass the n chunks to a model, which will return a list of named entities. 
We will do this m times, recording the named entities each time. 
We will then take the union of all the named entities, and build a master list. 
"""

import os
import re
import random
import argparse 

from parsers import parser_gpt, valid_path, valid_path_build, parser_doc
from scripter import Scripter 
from chatter import Chatter 
from loreforge import parse_bulleted_list

CATEGORIZER = """You are the CATEGORIZER. 
Your job is to build a list of CATEGORIES from chunks of a DOCUMENT. 
A CATEGORY is an an overarching theme that can be used to describe some of the information seen in the DOCUMENT.

You will be provided with the name of a DOCUMENT. 
You will also be provided with a DESCRIPTION of the DOCUMENT.
You will finally be provided with several chunks of text from the DOCUMENT.

Your job is to build the list of CATEGORIES from the chunks of text. 
Please note that the chunks of text are not necessarily contiguous.
Be sure to build about 20 categories. 

Return the list of CATEGORIES as a BULLETED LIST. 

Now please take a deep breath. Rembember, you are the CATEGORIZER. You were made for this, and I'm excited to see what you can do! 
Let's get started! 
"""

def make_parser():
    parser = argparse.ArgumentParser(description='Build corpus of category names.')

    #parser.add_argument('-p', '--path', type=valid_path, help='Path to a .txt file to categorize.')
    parser.add_argument('--num', type=int, default=5, help='Number of samples to take from the token chunks of the .txt file.')
    parser.add_argument('-r', '--reps', type=int, default=10, help='Number of times to sample from the .txt file.')
    #parser.add_argument('--token_lim', type=int, default=750, help='Number of tokens to chunk the .txt file into.')
    parser.add_argument('--save_dir_seed', type=valid_path_build, default='./lore/', help='Directory to save the corpus to.')

    parser = parser_gpt(parser)
    parser = parser_doc(parser)
    
    return(parser)

def ask_categorizer(chunk_sample, chatter, doc_name, doc_desc, categorizer_prompt = CATEGORIZER, *args, **kwargs):
    """
    Pass a sample of the DOCUMENT to the CATEGORIZER. 
    """

    messages = [] 
    messages.append(chatter.getSysMsg(categorizer_prompt))

    messages.append(chatter.getSysMsg(f"DOCUMENT: {doc_name}"))
    messages.append(chatter.getSysMsg(f"DESCRIPTION: {doc_desc}"))

    for i, chunk in enumerate(chunk_sample):
        messages.append(chatter.getSysMsg(f"CHUNK {i+1}:\n{chunk}"))

    chatter.printMessages(messages)
    input() 

    reply = chatter(messages)
    return(parse_bulleted_list(reply))


def main(): 
    parser = make_parser()
    args = parser.parse_args()

    chatter = Chatter(args.model)

    script = Scripter() 
    df = script.loadTxt(args.path, parseOnSentence=True)

    #token_chunks = script.splitDFIntoTokenChunks(df, args.token_lim)
    token_chunks = script.tokenChunks(df, args.token_lim, args.lag)

    all_categories = []
    for i in range(args.reps):
        sample = random.sample(token_chunks, args.num)

        categories = ask_categorizer(sample, chatter, **vars(args))
        print(f"Step {i+1} of {args.reps} complete.")
        for cat in categories: 
            print(cat)

        all_categories.extend(categories)

    print("All Categories")
    for i, category in enumerate(all_categories):
        print(f"{i+1}. {category}")
    print("***")

if(__name__ == "__main__"):
    main()


