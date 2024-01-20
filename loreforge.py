"""
We will use this project to build lore entries for NAMED ENTITIES in provided DOCUMENTS. 
"""

# Imports
import argparse 
import os

from chatter import Chatter 
from scripter import Scripter 
from noting import parse_bulleted_list
from parsers import parser_gpt, parser_sql, valid_path, valid_path_build
from colorcodes import Colorcodes as cc 

ENTITY_MASTER = """You are the ENTITY MASTER.
Your job is to find NAMED ENTITIES in a given snippet of INFORMATION. 

You will be provided with a snippet of INFORMATION. 
The INFORMATION may be accompanied by: 
- Document Name: The name of the document the INFORMATION was taken from.
- Document Description: A short description of the document the INFORMATION was taken from.

Your job is to parse the INFORMATION to find all NAMED ENTITIES. 

In this case, a NAMED ENTITY is a word or phrase that is a name of a PERSON, PLACE, THING, or IDEA.
We are breaking down manuals and technical documents, so be sure to be thorough. 
Also know that the INFORMATION may be poorly formatted, due to errors in the OCR process.
Please do your best to clean up the info where possible. 

You should output your findings as a BULLETED LIST. 

Now please take a deep breath and let's get started! 
"""

DISAMBIGUATOR_OLD = """You are the DISAMBIGUATOR.
Your job is to disambiguate NAMED ENTITIES against a given list of LORE ENTRIES. 

NAMED ENTITIES are entities that have been identitied from a snippet of INFORMATION. 
You may be provided with a DOCUMENT NAME, the name of the document the INFORMATION was taken from.
You may also be provided with a DOCUMENT DESCRIPTION, a short description of the document the INFORMATION was taken from.

LORE ENTRIES is a list of existing NAMED ENTITIES. 
The name of the LORE ENTRY describes the LORE contained in the file.
LORE ENTRIES are .txt documents stored locally. 

You should decide to which LORE ENTRY each NAMED ENTITY should be assigned. 
If no appropriate LORE ENTRY exists, you should create a new one.
LORE ENTRIES all end with .txt. They should be short and descriptive of the LORE. 
They should use underscores instead of spaces. They should be all lowercase. 

For each NAMED ENTITY provided, provide a LORE ENTRY. 
Output your response as a BULLETED LIST, where each bullet point is a LORE ENTRY.
"""

DISAMBIGUATOR = """You are the DISAMBIGUATOR.
Your job is to place NAMED ENTITIES into appropriate FILES. 

NAMED ENTITIES are entities identitied from a snippet of INFORMATION. 
You may be provided with a DOCUMENT NAME, the name of the document the INFORMATION was taken from.
You may also be provided with a DOCUMENT DESCRIPTION, a short description of the document the INFORMATION was taken from.

Each FILE in FILES is a .txt document defining information about a NAMED ENTITY.
For instance, dogs.txt may contain any information found from the DOCUMENT related to dogs. 

You should decide to which FILE each NAMED ENTITY should be assigned. 
If no appropriate FILE exists, you should create a new one.
FILES all end with .txt. They should use underscores instead of spaces. They should be all lowercase. 

For each NAMED ENTITY, assign a FILE.  
Output your response as a BULLETED LIST, with as many FILES as NAMED ENTITIES. 
"""

FORGE_MASTER = """You are the FORGE MASTER. 

"""

def make_parser():
    parser = argparse.ArgumentParser(description="Loreforge: A tool for generating lore entries for named entities in documents.")

    parser.add_argument('-p', '--path', help='Path to the document to be parsed.', required=True, type=valid_path)
    parser.add_argument('--lore_dir_seed', help='Path to the folder where the lore entries will be stored. (Default: ./lore)', default='./lore', type=valid_path_build)
    parser.add_argument('--token_lim', type=int, help='Chunk size the document will be split into. (Default: 1000)', default=1000)
    parser.add_argument('--lag', type=int, help='Number of tokens to lag between chunks. (Default: 0)', default=0)

    parser = parser_gpt(parser)
    parser = parser_sql(parser)

    return(parser)

def entitymaster_step(info, chatter, doc_name=None, doc_desc=None, entitymaster_prompt = ENTITY_MASTER):
    """
    This function performs a single interaction with the ENTITY MASTER (EM). 
    We use this to query the EM for the named entities in a given snippet of information, info. 
    We return these entities as a list. 
    """

    color = cc() 
    messages = [chatter.getSysMsg(entitymaster_prompt)]

    prompt = """Information:\n{}""".format(info)
    if doc_name:
        prompt += """\nDocument Name: {}""".format(doc_name)
    
    if doc_desc:
        prompt += """\nDocument Description: {}""".format(doc_desc)

    messages.append(chatter.getUsrMsg(prompt))
    reply = chatter(messages)

    reply = parse_bulleted_list(reply)
    return(reply)

def disambiguator_step(named_entities, lore_entries, chatter, disambiguator_prompt = DISAMBIGUATOR):
    """
    This function performs a single interaction with the DISAMBIGUATOR (DIS).
    We use this to query the DIS for the lore entry for each named entity in named_entities.
    We return these lore entries as a list. 
    """

    messages = [chatter.getSysMsg(disambiguator_prompt)]

    prompt = """NAMED ENTITIES:\n{}""".format('\n'.join(named_entities))
    messages.append(chatter.getUsrMsg(prompt))

    prompt = """LORE ENTRIES:\n{}""".format('\n'.join(lore_entries))
    messages.append(chatter.getUsrMsg(prompt))

    chatter.printMessages(messages)
    input('Continue?') 

    reply = chatter(messages)

    reply = parse_bulleted_list(reply)
    return(reply)

def forge_step(info, chatter, lore_dir='./lore', doc_name=None, doc_desc=None, entitymaster_prompt = ENTITY_MASTER):
    color = cc() 
    existing_lore = os.listdir(lore_dir)

    # Ask the entity master for named entities in the given information
    print(color.pred('Grabbing Entities...'))
    named_entities = entitymaster_step(info, chatter, doc_name=doc_name, doc_desc=doc_desc, entitymaster_prompt=entitymaster_prompt)

    print("Named Entities:")
    for ne in named_entities:
        print(ne)
    print("***************")
    print() 

    lore_entries = named_entities 
    if(len(existing_lore)):
        # Ask the disambiguator for lore entries for each named entity
        print(color.pred('Disambiguating Entities...')) 
        lore_entries = disambiguator_step(named_entities, existing_lore, chatter)

        for named_entity, lore_entry in zip(named_entities, lore_entries):
            print("Named Entity: {}".format(named_entity))
            print("Lore Entry: {}".format(lore_entry))
            print("")

        input() 

    # Use the Forge Master to load the information into the appropriate lore entries. 
    


def build_lore_dir(args):
    lore_dir = os.path.join(args.lore_dir_seed, args.path.split('/')[-1])
    if(not os.path.exists(lore_dir)):
        try:
            os.makedirs(lore_dir)
        except Exception as e:
            print(e)
            print("Failed to create lore directory at {}".format(lore_dir))
            exit(1)

    return(lore_dir)
    

def main():
    parser = make_parser()
    args = parser.parse_args()

    args.lore_dir = build_lore_dir(args)
    print("Lore Dir: {}".format(args.lore_dir))
    
    script = Scripter()
    df = script.loadTxt(args.path)
    token_chunks = script.splitDFIntoTokenChunks(df, args.token_lim, lag=args.lag)

    chatter = Chatter(args.model)
    for chunk in token_chunks: 
        chunk = script.getText(chunk)
        print(chunk)

        forge_step(chunk, chatter, lore_dir=args.lore_dir, doc_name=args.path.split('/')[-1])




    



if __name__ == "__main__":
    main()