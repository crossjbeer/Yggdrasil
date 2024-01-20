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
Also know that the INFORMATION may be poorly formatted. Most commonly, words have spaces where there shouldn't be. 
Please do your best to clean up the info where possible. 

You should output your findings as a BULLETED LIST. 
Each named entity should be lowercase and use underscores instead of spaces.

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
You are an expert researcher and writer. 

You will be provided with a small list of NAMED ENTITIES. 
You will also be provided with a snippet of INFORMATION.
You may be provided with a DOCUMENT NAME, the name of the document the INFORMATION was taken from.
You may also be provided with a DOCUMENT DESCRIPTION, a short description of the document the INFORMATION was taken from.

We want to pull any information related to each entity from the list.
Your job is to read through a snippet of INFORMATION and write an entry for each NAMED ENTITY. 

For each entity, please output your response as follows: 
- Entity: <ENTITY>
- Info: <INFO>
"""

def make_parser():
    parser = argparse.ArgumentParser(description="Loreforge: A tool for generating lore entries for named entities in documents.")

    parser.add_argument('-p', '--path', help='Path to the document to be parsed.', required=True, type=valid_path)
    parser.add_argument('--lore_dir_seed', help='Path to the folder where the lore entries will be stored. (Default: ./lore)', default='./lore', type=valid_path_build)
    parser.add_argument('--token_lim', type=int, help='Chunk size the document will be split into. (Default: 1000)', default=1000)
    parser.add_argument('--lag', type=int, help='Number of tokens to lag between chunks. (Default: 0)', default=0)

    parser.add_argument('--doc_name', help='Name of the document to be parsed.', default=None, type=str)
    parser.add_argument('--doc_desc', help='Description of the document to be parsed.', default=None, type=str)

    parser.add_argument('--delete_lore', help='Delete existing lore entires', action='store_true')

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
    #print(reply)
    #input("EM REPLY ^^")

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

    reply = chatter(messages)

    #print(reply)
    #input("DIS REPLY ^^")

    reply = parse_bulleted_list(reply)
    reply = [i.split('.')[0] if i.endswith('.txt') else i for i in reply]

    return(reply)

def parse_forgemaster(reply):
    entity_to_info = {}

    reply = reply.split('\n')
    for line in reply: 
        if(line.startswith('Entity:')):
            entity = line.split('Entity:')[1].strip()
            entity_to_info[entity] = ''

        elif(line.startswith('Info:') and entity):
            info = line.split('Info:')[1].strip()
            entity_to_info[entity] = info
            entity = None 

    return(entity_to_info)

def forgemaster_step(named_entities, info, chatter, forgemaster_prompt = FORGE_MASTER):
    """
    This function performs a single interaction with the FORGE MASTER (FM).
    We use FM to load the information into the appropriate files. 
    """

    messages = [chatter.getSysMsg(forgemaster_prompt)]

    prompt = """NAMED ENTITIES:\n{}""".format('\n'.join(named_entities))
    messages.append(chatter.getUsrMsg(prompt))

    prompt = """INFORMATION:\n{}""".format(info)
    messages.append(chatter.getUsrMsg(prompt))

    reply = chatter(messages)

    print(reply)

    reply = parse_forgemaster(reply)
    for entity in reply:
        print("Entity: {}".format(entity))
        print("Info: {}".format(reply[entity]))
        print()

    #input() 

    #reply = parse_bulleted_list(reply)
    return(reply)

def forge_step(info, chatter, lore_dir='./lore', doc_name=None, doc_desc=None, entitymaster_prompt = ENTITY_MASTER, disambiguator_prompt=DISAMBIGUATOR, forgemaster_prompt=FORGE_MASTER, forgemaster_entities=5, *args, **kwargs):
    color = cc() 
    existing_lore = os.listdir(lore_dir)

    # Ask the entity master for named entities in the given information
    print(color.pred('Grabbing Entities...'))
    named_entities = entitymaster_step(info, chatter, doc_name=doc_name, doc_desc=doc_desc, entitymaster_prompt=entitymaster_prompt)

    if(len(existing_lore)):
        existing_lore = [i for i in existing_lore if i.endswith('.txt')]
        existing_lore = [i.split('.')[0] for i in existing_lore]

        # Ask the disambiguator for lore entries for each named entity
        print(color.pred('Disambiguating Entities...')) 
        named_entities = disambiguator_step(named_entities, existing_lore, chatter, disambiguator_prompt=disambiguator_prompt)

        input() 

    print("Named Entities:")
    for ne in named_entities: 
        print(ne)
        pth = os.path.join(lore_dir, ne+'.txt')

        if(ne not in existing_lore):
            with open(pth, 'w') as f:
                f.write('# File to store information about [{}]\n'.format(ne))

    # Use the Forge Master to load the information into the appropriate lore entries. 
    for i in range(0, len(named_entities), forgemaster_entities):
        current_entites = named_entities[i:min(i+forgemaster_entities, len(named_entities)-1)]

        print("CURRENT ENTITIES:")
        print(current_entites)

        entity_to_info = forgemaster_step(current_entites, info, chatter, forgemaster_prompt=forgemaster_prompt)

        for entity, info in entity_to_info.items():
            pth = os.path.join(lore_dir, entity+'.txt')

            with open(pth, 'a') as f:
                f.write('\n'+info)

        


    


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

    if(args.delete_lore):
        print("Deleting existing lore...")
        for f in os.listdir(args.lore_dir):
            os.remove(os.path.join(args.lore_dir, f)) if f.endswith('.txt') else None
    
    script = Scripter()
    df = script.loadTxt(args.path)
    token_chunks = script.splitDFIntoTokenChunks(df, args.token_lim, lag=args.lag)

    chatter = Chatter(args.model)
    for chunk in token_chunks: 
        chunk = script.getText(chunk)
        print("CHUNK ***")
        print(chunk)
        print("************")
        #input() 

        forge_step(chunk, chatter, **vars(args))




    



if __name__ == "__main__":
    main()