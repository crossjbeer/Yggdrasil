import random
import argparse 

from parsers import parser_gpt, valid_path, valid_path_build, parser_doc
from scripter import Scripter 
from chatter import Chatter 
from loreforge import parse_bulleted_list

CATEGORIZER = """You are the CATEGORIZER. 
Your job is to build a list of CATEGORIES from chunks of a DOCUMENT. 
A CATEGORY is an an overarching theme that can be used to describe some of the information seen in the DOCUMENT.
Think of your CATEGORIES as an index for the DOCUMENT, constructed from the chunks of text in the DOCUMENT.

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

DISAMBIGUATOR1 = """You are the DISAMBIGUATOR.
Your job is to disambiguate the CATEGORIES that the CATEGORIZER has built.
A CATEGORY is an an overarching theme that can be used to describe some information seen in a DOCUMENT. 

You will be provided with the following: 
- A list of CATEGORIES that the CATEGORIZER has built.
- The name of the DOCUMENT that the CATEGORIZER has built the CATEGORIES from.
- A DESCRIPTION of the DOCUMENT that the CATEGORIZER has built the CATEGORIES from.

Your job is to disambiguate the CATEGORIES.
Make sure you write at least 250 categories.
Please return the disambiguated CATEGORIES as a BULLETED LIST.
"""

DISAMBIGUATOR = """You are the DISAMBIGUATOR. 
Your job is to create a master list of categories from the CATEGORIES that the CATEGORIZER has built.

You will be provided with the following: 
- A list of CATEGORIES that the CATEGORIZER has built. 
- The namof of the DOCUMENT that the CATEGORIZER has built the CATEGORIES from.
- A DESCRIPTION of the DOCUMENT that the CATEGORIZER has built the CATEGORIES from.

Your job is to create a master list of categories from the CATEGORIES that the CATEGORIZER has built.
Make at least 50 categories. 
All categories should be lowercase and use underscores instead of spaces. 
Categories should be as general as possible. 
Please return your categories as a BULLETED LIST. 

"""

def make_parser():
    parser = argparse.ArgumentParser(description='Build corpus of category names.')

    parser.add_argument('--num', type=int, default=5, help='Number of samples to take from the token chunks of the .txt file.')
    parser.add_argument('-r', '--reps', type=int, default=10, help='Number of times to sample from the .txt file.')
    parser.add_argument('--save_dir_seed', type=valid_path_build, default='./lore/', help='Directory to save the corpus to.')

    parser = parser_gpt(parser)
    parser = parser_doc(parser)
    
    return(parser)

def ask_disambiguator(categories, chatter, doc_name, doc_desc, disambiguator_prompt = DISAMBIGUATOR, *args, **kwargs):
    """
    Pass a list of CATEGORIES to the DISAMBIGUATOR. 
    """

    messages = [] 
    messages.append(chatter.getSysMsg(disambiguator_prompt))

    msg = "CATEGORIES:\n"
    for i, category in enumerate(categories):
        msg += f"{i+1}. {category}\n"
    messages.append(chatter.getSysMsg(msg))

    messages.append(chatter.getSysMsg(f"DOCUMENT: {doc_name}"))
    messages.append(chatter.getSysMsg(f"DESCRIPTION: {doc_desc}"))

    #chatter.printMessages(messages)
    #input() 

    reply = chatter(messages)
    return(parse_bulleted_list(reply))

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

    #chatter.printMessages(messages)
    #input() 

    reply = chatter(messages)
    return(parse_bulleted_list(reply))


def main(): 
    parser = make_parser()
    args = parser.parse_args()

    chatter = Chatter(args.model)

    script = Scripter() 
    df = script.loadTxt(args.path, parseOnSentence=True)
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
    #print("***")

    #disambiguated_categories = ask_disambiguator(all_categories, chatter, **vars(args))
    disambiguated_categories = ask_disambiguator(all_categories, Chatter('gpt-4'), **vars(args))

    print("Disambiguated Categories")
    for i, category in enumerate(disambiguated_categories):
        print(f"{i+1}. {category}")

    input() 

    #from scripter import jaccard_distance
    #for category in categories: 
    #    all_distances = {i: jaccard_distance(category, i) for i in all_categories if i != category}

    #    print(f"{category}:\n")
    #    for i in sorted(all_distances, key=all_distances.get):
    #        print(f"{i}: {all_distances[i]}")



if(__name__ == "__main__"):
    main()


