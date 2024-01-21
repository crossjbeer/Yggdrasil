# Imports
import argparse 
import os

from chatter import Chatter 
from scripter import Scripter 
from noting import parse_bulleted_list
from parsers import parser_gpt, parser_sql, valid_path, valid_path_build
from colorcodes import Colorcodes as cc 
import re

ENTITY_MASTER = """You are the ENTITY MASTER.
You are an expert writer and researcher.

Your job is to find NAMED ENTITIES in a given snippet of INFORMATION. 
A NAMED ENTITY is a word or phrase that is a name of a PERSON, PLACE, THING, or IDEA.

You will be provided with a snippet of INFORMATION. 
The INFORMATION may be accompanied by: 
- Document Name: The document the INFORMATION was taken from.
- Document Description: A short description of the document.

Your job is to find all NAMED ENTITIES in the INFORMATION. 
You should also gather all details that are relevant to each NAMED ENTITY.
Write them as a bulleted list.

Be thorough. 
Include factual information, such as values, numbers, and rules. 
You may remove unnecesasry flavor text.
We are trying to condense this information. 

DO NOT MAKE 'sub entities'.
There is no such thing as a Sub-Entity in our framework. 
Instead, just make another 'Entity'. 

Also know that the INFORMATION may be poorly formatted. Most commonly, words have spaces where there shouldn't be. 
Please do your best to clean up the info where possible. 

Once you have found all NAMED ENTITIES, and organized the relevant information, you should output your findings.
For each NAMED ENTITY, you should output with the following format: 
- Entity: <ENTITY>
- <Relevant information 1>
- <Relevant information 2>
- ... 
- <Relevant information N>

Each <ENTITY> should be lowercase and use underscores instead of spaces.

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
Your job is to assign NAMED ENTITIES to FILES. 
NAMED ENTITIES are PEOPLE, PLACES, THINGS, and IDEAS. 

You will be provided with a list of NAMED ENTITIES.
You will also be provided with a list of FILES.

File names are named entities. 
For instance, a file named 'dogs' contains information about dogs. 

Example of an interaction: 
FILES: ['dogs', 'dobermen', 'cats', 'birds']
NAMED ENTITIES: ['dog', 'cat', 'chihuahua']

Output: 
- dogs
- cats
- chihuahuas

If you were to be provided with the NAMED ENTITY 'dog', you should assign it to the FILE 'dogs'.
However, if you were provided with the NAMED ENTITY 'doberman', you should assign it to the file 'doberman'.
Maintain file name conventions. 
They should be lowercase, and use underscores instead of spaces.

You may also be provided with: 
- DOCUMENT NAME: The name of the document the ENTITIES were taken from.
- DOCUMENT DESCRIPTION: A short description of the document. 

For each NAMED ENTITY, you decide if an appropriate FILE exists. 
If not, use the name of the NAMED ENTITY to create a new FILE.
If a FILE exists, assign the NAMED ENTITY to that FILE.

Output your response as a bulleted list, with as many bullets as NAMED ENTITIES.
"""

FORGE_MASTER = """You are the FORGE MASTER.  : 

You are an expert researcher and writer. 

You will be provided with a small list of NAMED ENTITIES. 
You will also be provided with a snippet of INFORMATION.
You may be provided with a DOCUMENT NAME, the name of the document the INFORMATION was taken from.
You may also be provided with a DOCUMENT DESCRIPTION, a short description of the document the INFORMATION was taken from.

You should find any information related to each entity from the list.
For each NAMED ENTITY, read through the INFORMATION. Find any information related to the NAMED ENTITY.
If none is found, do not write anything for that entry. 

If information is found, condense the relevant information. 
Be sure to be thorough. 
Output your response as follows: 
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

def parse_entitymaster(reply):
    named_entities = {}

    reply = reply.split('\n')
    entity = None 
    for line in reply:
        if re.match(r'^(\t*-|-)', line):
            if line.startswith('\t'):
                line = line.lstrip('\t')
                line = line.strip() 
            line = line.lstrip('-')
            line = line.strip() 

            if(line.startswith('Entity:')):
                entity = line.split('Entity:')[1].strip()
                named_entities[entity] = []
            elif(entity):
                named_entities[entity].append(line)

    return named_entities

def entitymaster_step(info, chatter, doc_name=None, doc_desc=None, entitymaster_prompt = ENTITY_MASTER):
    """
    This function performs a single interaction with the ENTITY MASTER (EM). 
    We use this to query the EM for the named entities in a given snippet of information, info. 
    We return these entities as a list. 
    """

    messages = [chatter.getSysMsg(entitymaster_prompt)]

    prompt = """Information:\n{}""".format(info)
    if doc_name:
        prompt += """\nDocument Name: {}""".format(doc_name)
    
    if doc_desc:
        prompt += """\nDocument Description: {}""".format(doc_desc)

    messages.append(chatter.getUsrMsg(prompt))
    reply = chatter(messages)

    print(reply)
    input("EM REPLY ^^")

    reply = parse_entitymaster(reply)

    return(reply)

def disambiguator_step(named_entities, lore_entries, chatter, disambiguator_prompt = DISAMBIGUATOR):
    """
    This function performs a single interaction with the DISAMBIGUATOR (DIS).
    We use this to query the DIS for the lore entry for each named entity in named_entities.
    We return these lore entries as a list. 
    """

    messages = [chatter.getSysMsg(disambiguator_prompt)]

    #prompt = """NAMED ENTITIES:\n{}""".format('\n'.join(named_entities))
    prompt = f"""NAMED ENTITIES: {named_entities}"""
    messages.append(chatter.getUsrMsg(prompt))

    file_str = "["
    for file in lore_entries: 
        file_str += f"'{file}', "
    file_str = file_str[:-2] + "]"
    prompt = f"""FILES: {file_str}"""
    messages.append(chatter.getUsrMsg(prompt))

    chatter.printMessages(messages)

    reply = chatter(messages)

    print(reply)
    input("DIS REPLY ^^")

    reply = parse_bulleted_list(reply)

    print(reply)
    input("PARSE REPLY &")

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
    print("FM REPLY ^^")

    reply = parse_forgemaster(reply)
    for entity in reply:
        print("Entity: {}".format(entity))
        print("Info: {}".format(reply[entity]))
        print()

    return(reply)

def grab_existing_lore(lore_dir):
    existing_lore = os.listdir(lore_dir)
    existing_lore = [i.split('.')[0] for i in existing_lore if i.endswith('.txt')]

    return(existing_lore)

def forge_step(info, chatter, lore_dir='./lore', doc_name=None, doc_desc=None, entitymaster_prompt = ENTITY_MASTER, disambiguator_prompt=DISAMBIGUATOR, forgemaster_prompt=FORGE_MASTER, forgemaster_entities=5, *args, **kwargs):
    color = cc() 
    
    # Ask the entity master for named entities in the given information
    print(color.pred('Grabbing Entities...'))
    named_entities = entitymaster_step(info, chatter, doc_name=doc_name, doc_desc=doc_desc, entitymaster_prompt=entitymaster_prompt)

    print("Named Entities:")
    for named_entity, info in named_entities.items():
        print("Entity: {}".format(named_entity))
        print("Info:\n{}".format("\n".join(info)))
        print()

    input('Continue?') 

    existing_lore = grab_existing_lore(lore_dir)

    print("Existing Lore:")
    print(existing_lore)
    input('Continue?')

    if(len(existing_lore)):
        entities = list(named_entities.keys())
        for i in range(0, len(entities), forgemaster_entities):
            current_entities = entities[i:min(i+forgemaster_entities, len(entities)-1)]
            lore_entries = disambiguator_step(current_entities, existing_lore, chatter, disambiguator_prompt=disambiguator_prompt)

            entity_to_lore = {i:j for i,j in zip(current_entities, lore_entries)}
            for entity in entity_to_lore:
                lore = entity_to_lore[entity]
                if(lore in existing_lore):
                    with open(os.path.join(lore_dir, lore+'.txt'), 'a') as f:
                        f.write('\n'+'\n'.join(named_entities[entity]))

                else:
                    print("Creating new lore entry for {}".format(entity))
                    pth = os.path.join(lore_dir, lore+'.txt')
                    with open(pth, 'w') as f:
                        f.write('\n'.join(named_entities[entity]))
            
            existing_lore = grab_existing_lore(lore_dir)

    else: 
        print("Named Entities:")
        for named_entity, info in named_entities.items():
            print("Entity: {}".format(named_entity))
            print("Info:\n{}".format("\n".join(info)))
            
            if(len(info)):
                print("Creating new lore entry for {}".format(named_entity))
                pth = os.path.join(lore_dir, named_entity+'.txt')
                with open(pth, 'w') as f:
                    f.write('\n'.join(info))
    


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