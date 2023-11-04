__doc__ = """
The Oghma module is used to read, maintain, organize, and learn from DND Campaign Notes. 
The notes given can include information such as: 
1) world lore
2) character information
3) campaign details
4) monsters
5) locations
6) spells
7) items
8) etc

If a note is provided, Oghma takes the following steps :
1) calculates a hash index for the note's content
-- we use this to look for changes to this note down the line
2) Ingests the content of the note
3) adds the note to the 'timeline' of the given campaign...
"""


import argparse 
import psycopg2
#import mysql.connector 
import os 
import hashlib 
import numpy as np 
import json 

from scripter import Scripter 
from chatter import Chatter 

FORBIDDEN = [
    'None', 'none', 'Unknown at this point', 'Not mentioned', 'None mentioned'
]


SYSTEM_MSG = """
You are a near perfect AI with many personas. Today, you are DNDGPT. You are knowledgable and interested in the game dungeons and dragons, its gameplay, lore, worldbuilding, and everything else therein.
"""

SETUP_MSGS = [] 

SETUP_MSG = """
We will organize information about a dungeons and dragons world.
We will start with some notes related to a dungeons and dragons campaign.
We will end with a list of named entities relevant to dungeons and dragons.
We will solve this problem in several steps, which are as follows: 

Steps: 
1) Read the note snippet 
2) Create a prompt which will instruct an LLM to effectively condense the note information.
3) Read through the condensed information. 
4) Create a prompt to instruct an LLM to extract as many relevant entities to dnd, 
-- Available categories are: 
-- a) adventuring, 
-- b) world building, 
-- c) characters, 
-- d) locations, 
-- e) abilities, 
-- f) actions, 
-- g) spells, 
-- h) items, 
5) Evaluate the final result and refine if necessary.
""" 

"""
We will organize information about a dungeons and dragons world.
We will start with some notes related to a dungeons and dragons campaign.
We will end with a list of named entities relevant to dungeons and dragons.
We will solve this problem in several steps, which are as follows: 

Steps: 
1) Read the note snippet 
2) Create a prompt to refine the data to remove unnecessary information and make it more easily readable for ChatGPT
3) Use the created prompt to prompt chatgpt to refine the data
4) Read through the refined data
5) Create a prompt for gpt-4 to instruct the model to extract as many relevant entities to dnd, including adventuring, world building, characters, locations, abilities, actions, spells, items, etc. 
6) Produce the final result.
""" 

S1 = """
STEP 1 : Read through the following notes:
"""

S2 = """
STEP 2: Create a prompt which will instruct an LLM to effectively condense the note information.
"""

S3 = """
STEP 3: Read through the condensed information. 
"""

S4 = """
STEP 4: Create a prompt to instruct an LLM to extract as many relevant entities to dnd, including adventuring, world building, characters, locations, abilities, actions, spells, items, etc. 
Format your response as:
Adventuring:
- relevant point 1
World Building: 
- relevant point 2
...
"""

S5 = """
STEP 5: Evaluate the final result and refine if necessary.
"""


"""
The task is to extract as many as possible relevant entities to dnd, adventuring, world building, and more.
The entities should include all characters, locations, abilities, actions, spells, items, etc.
All entities should have a list of associated metadata, included in () next to the name.

An example "St. Peter is located in Paris" should have an output with the following format
 
entity
St. Peter (person)
Paris (location)
"""

"""
The task is to extract as many relevant entities to dnd, adventuring, world building, and more.
The entities should include all characters, locations, abilities, actions, spells, items, etc.
Also, return the type of an entity using the Wikipedia class system 
Additionally, extract all relevant relationships between identified entities.
The relationships should follow the Wikipedia schema type.
The output of a relationship should be in a form of a triple Head, Relationship, Tail, for example
Peter, WORKS_AT, Hospital/n
 An example "St. Peter is located in Paris" should have an output with the following format
 
entity
St. Peter, person
Paris, location

relationships
St.Peter, LOCATED_IN, Paris
"""


SECTIONER_MSG1 = """
Please read the following snippet of DND notes. 
Identify segments of information.
For each segment: 
    format the segment using JSON Schema.
    Export each segment using the given function EXPORT_INFO.
"""

SECTIONER_FUNC1 = {
    'name': 'EXPORT_INFO',
    'description': 'Export section of note information with json formatting',
    'parameters': {
        'type': 'object',
        'properties': {
            'text': {
                'type': 'string',
                'description': 'string of formatted json text'
            }
        }, 
        'required': ['text']
    }
}


SETUP_MSG1 = """
We will organize information about a dungeons and dragons world.
We will start with some notes related to a dungeons and dragons campaign.
We will end with a list of named entities relevant to dungeons and dragons.
We will solve this problem in several steps, which are as follows: 

Steps: 
1) Read the note snippet 
2) Extract as many entities relevant to DND as possible. 
-- Each entity should fall into one of the following categories: 
World Lore
Backstory
Campaign Setting
Locations
Cultural History
Character Lore
Player Character (PC)
Non-Player Character (NPC)
Character Development
Abilities
Actions
Spells
Items
Quests
Side Quests
Factions
Organizations
Adventure Hooks 
World Economy
Politics
Religion
Geography
Climate
Treasure
Rewards
Races
Species
Histories
Story Arcs
Languages and Dialects
Landmarks
Town/City Design
Themes
Moral Dilemmas
Legends
Myths

Format each category as:
''' 
<category name>:
\t- <entity name>
\t- <entity name>
\t- ...
'''

-- Each entity entry should be SIMPLE, including ONLY a name. 
-- Each entity's name should be listed under one or more of the categories
"""

SETUP_MSG2 = """
You should use the note snippet + note name above. 
Scrape NAMED ENTITIES relevant to the campaign.
For EACH NAMED ENTITY, place it under the appropriate ENTITY CATEGORY.

REQUIREMENTS: 
-- ENTITIES are SIMPLE, including ONLY a name. 
-- ENTITIES may be listed under MULTIPLE CATEGORIES. 
-- IMPORTANT: If category has no ENTITY, please write '- None' ONLY

Format each category as:

<category name>:
- <entity name>
- <entity name>
- ...

NAMED ENTITY CATEGORIES: 
World Lore
Locations
Names
Characters
Abilities
Actions
Spells
Items
Quests
Side Quests
Factions
Organizations
Adventure Hooks 
Economy
Politics
Religion
Geography
Treasure
Rewards
Races
Species
Histories
Languages
Landmarks
Themes
Legends
"""

SETUP_MSG3 = """
You should use the note snippet + note name above. 
Scrape NAMED ENTITIES relevant to this dnd campaign.

REQUIREMENTS: 
-- ENTITIES are SIMPLE, including ONLY a name. 
"""
"""
Format each category as:

<category name>:
- <entity name 1>
- <entity name 2>
- <entity name 3>
- ...
- <entity name n>

NAMED ENTITY CATEGORIES: 

Characters
Locations
Abilities
Actions
Spells
Items
Religion
Geography
Treasure
Rewards
Races
Species
Histories
Languages
Landmarks
Themes
Legends
"""


GRAPH_MSG = """
Build knowledge graph entries.
Build entries for ONLY the given entity.

The information for the graph will be given as a note from a dnd campaign.
Extract as many relevant relationships connected to that entity.
DO NOT INFER. DO NOT include relationships not mentioned in the notes.

The relationships should follow the Wikipedia schema type.
The output of a relationship should be in a form of a triple Head, Relationship, Tail, with () around any metadata.

Example
```
Note: 
Skullgang owns a red mask

Entity + Tags:
- Skullgang
\t- Player Character
\t- Party Member

Relationships: 
Skullgang, OWNS, mask (red)\n
...

END_CHAR
```
"""


def make_parser():
    parser = argparse.ArgumentParser(description='File Differences Checker')
    parser.add_argument('-H', '--host', type=str, default='localhost', help='Host name (default: localhost)')
    parser.add_argument('-d', '--database', type=str, default='yggdrasil', help='Database name (default: yggdrasil)')
    parser.add_argument('-u', '--user', type=str, default='ygg', help='User name (default: ygg)')
    parser.add_argument('-p', '--password', type=str, default='ygg', help='Password (default: ygg)')
    parser.add_argument('-t', '--table', type=str, default='notes', help='Table name (default: notes)')
    parser.add_argument('-n', '--note', type=str, default='', help='Note (default: empty)')
    parser.add_argument('-m', '--model', type=str, help='GPT Model to use [gpt-3.5-turbo, gpt-4, gpt-3.5-turbo-16k]', default='gpt-3.5-turbo-16k')
    parser.add_argument('--clean', help='Clean text to anonymized and stripped', action='store_true')
    parser.add_argument("--stopword", help='Remove stopwords', action='store_true')
    parser.add_argument('--tokenlim', help='Limit for each batch, in tokens.', default=2000, type=int)

    parser.add_argument('--lag', help='Number of lines to lag behind token chunk calculation', default=0, type=int)
    parser.add_argument('--lead', help='Number of lines to lead ahead token chunk calculation', default=0, type=int)

    parser.add_argument('--halt', action="store_true", help='Will pause before sending each prompt')
    return parser



def make_connection_mysql(host, db, user, pswd):
    connection = mysql.connector.connect(
        host = host,
        user = user,
        password = pswd, 
        database = db
    )

    return(connection)

def make_connection_postgresql(host, db, user, pswd):
    connection = psycopg2.connect(
        host=host,
        user=user,
        password=pswd,
        dbname=db
    )

    return connection

def get_note(path):
    if(not os.path.exists(path)):
        print("Given Note Path [{}] Doesn't Exist...".format(path))
        return(None, None)

    name = path 
    if('/'):
        name = path.split("/")[-1]

    return(open(path, 'r'), name)

def calc_hash(content):
    hash_value = hashlib.md5(content.encode('utf-8')).hexdigest()
    return hash_value

def get_hash_from_table(path, name, table, connection):
    query = f"SELECT hash FROM {table} WHERE path = %s AND name = %s;"

    cursor = connection.cursor() 
    cursor.execute(query, (path, name))

    result = cursor.fetchone() 

    hash_val = None 
    if(result):
        hash_val = result[0]

    return(hash_val)

def update_hash(path, name, table, connection, hash):
    #query = f"UPDATE ONE hash FROM {table} WHERE path = %s AND name = %s;"
    query = f"INSERT INTO {table} (path, name, hash) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE hash = VALUES(hash)"

    cursor = connection.cursor() 
    cursor.execute(query, (path, name, hash))

    connection.commit()
    cursor.close()
    return()


def export_info(text, path='./oghma_test.txt'):
    if(os.path.exists(path)):
        f = open(path, 'a')
    else:
        f = open(path, 'w')

    f.write(text)
    f.write('\n')
    f.close()
    return()




def save_dict_to_txt(dictionary, file_path):
    try:
        # Convert the dictionary to a human-readable string using json.dumps()
        dict_str = json.dumps(dictionary, indent=4)
        
        # Open the file in write mode and save the string representation of the dictionary.
        with open(file_path, 'w') as file:
            file.write(dict_str)
        print("Dictionary saved to:", file_path)
    except Exception as e:
        print("Error saving the dictionary:", e)

def save_dict_to_json(dct, path):
    try:
        with open(path, "w") as outfile:
            json.dump(dct, outfile)

    except Exception as e: 
        print("Prob Saving Summary Json")
        print(e)
        exit()

    return()

def combine_processed_reply(allreply, reply):
    for k in reply:
        if(len(allreply) and k in allreply):
            allreply[k] += reply[k]
            allreply[k] = list(np.unique(allreply[k]))
        else:
            allreply[k] = reply[k]

    return(allreply)

def process_reply(data, forbidden=FORBIDDEN):
    lines = data.strip().split('\n')
    result = {}
    current_header = None

    for line in lines:
        if(not line):
            continue 

        if(line[0] != '-' and ':' in line):
            current_header = line.split(":")[0]
            continue 

        if(current_header):
            line = line.strip()
            if(line[0] == '-'):
                centry = " ".join(line.split('-')[1:]).strip()

                if(centry in forbidden):
                    continue 

                if(current_header not in result):
                    result[current_header] = [centry]
                else:
                    result[current_header].append(centry)

    # Remove headers with no remaining lines
    result = {k: v for k, v in result.items() if v}

    return result

def scrape_note_for_categories_and_entities(notepath, notename, model, tokenlim, clean=False, stopword=False, lag=0, lead=0):
    chat = Chatter(model)

    script = Scripter()
    script.loadTokenizer(model)
    
    df = script.loadTxt(notepath)
    if(clean):
        df = script.cleanDFPipe(df, stopword=stopword)

    line_list = df['text'].to_list()

    final_replies = [] 
    #all_reply = {}
    all_reply = ""
    for i,j in script.getAllTokenChunkBounds(df, tokenlim):
        i = max(0, i-lag)
        j = min(len(line_list), j+lead)

        lines = line_list[i:j]

        messages = []

        messages.append({"role":"system", "content":SYSTEM_MSG})
        messages.append({'role':'user', 'content':'CONTEXT - Note Snippet:'})
        messages.append({'role':'user', 'content':"```" + "\n".join(lines) + "```"})
        messages.append({'role':'user', 'content':'For extra content, the file name of this note is: {}'.format(notename)})
        #messages.append({'role':'user', 'content':SETUP_MSG2})
        messages.append({'role':'user', 'content':SETUP_MSG3})

        chat.printMessages(messages)
        #input()

        #reply = chat.passMessagesGetReply(messages)
        #print(reply)
        #input()
        #processed_reply = process_reply(reply)
        #replyList = reply.split("\n")

        #final_replies.append(reply)
        #all_reply = combine_processed_reply(all_reply, processed_reply)
        #all_reply += reply + "\n"

    #save_dict_to_json(all_reply, os.path.join(notepath.split('/')[:-1], notename + '.json'))
    #with open("./oghma_test.txt", 'w') as wf:
    #    wf.write(all_reply)

    f = open('./oghma_test.txt', 'r')
    all_reply = "\n".join(f.readlines())

    messages= []
    messages.append(chat.getSysMsg(SYSTEM_MSG))
    messages.append(chat.getUsrMsg("""Please deobfuscate this list of entities. Please return them as a simple bulleted list. Please also include any entites you didn't deobfuscate"""))
    messages.append(chat.getUsrMsg(all_reply))

    reply = chat.passMessagesGetReply(messages)
    print(reply)
    input("REPLY ^")

    return()

#def deobfuscate_replies()



def refine_processed_note(processed_note_str, model):
    chat = Chatter(model)

    messages = [] 

    messages.append({'role':'system', 'content':'You are FormatGPT.'})
    messages.append({'role':'user', 'content':"""
The following is a list of categories and entries. These have the form:
    ```
    Category:
        - Entry
        - Entry.
    ```
                     
This information is alright but has some problems.
There are duplicate entries. There are also categories with no valid entries.

Thinking in steps as you go, please accomplish the following task:
1) remove any categories without information (saying 'none mentioned' or 'na' doesn't count as information)
2) remove any unspecific category entries. Things like 'campaign' or 'change' should be dropped.
3) remove any categories with no entries
"""})
    
    messages.append({'role':'user', 'content':processed_note_str})

    reply = chat.passMessagesGetReply(messages)

    reply_dict = process_reply(reply)

    for header in reply_dict:
        print(header)
        for v in reply_dict[header]:
            print("\t- {}".format(v))
    input()

    return(reply_dict)

def refined_note_to_tags(refined_note):
    cnt = {}
    for k in refined_note:
        for kk in refined_note[k]:
            if(kk in cnt):
                cnt[kk].append(k)
            else:
                cnt[kk] = [k]

    return(cnt)

def build_entries_from_entities(entities, notepath, model, clean, stopword):
    chat = Chatter(model)

    script = Scripter()
    script.loadTokenizer(model)
    
    df = script.loadTxt(notepath)
    if(clean):
        df = script.cleanDFPipe(df, stopword=stopword)

    line_list = df['text'].to_list()
    note_str = ' '.join(line_list)
    note_name = notepath.split("/")[-1]

    for entity in entities:
        messages = []

        #messages.append({'role':'system', 'content': SYSTEM_MSG})
        messages.append({'role':'user', 'content': 'CONTEXT - DND Notes:'})
        messages.append({'role':'user', 'content': note_str})
        messages.append({'role':'user', 'content': 'CONTEXT - Note filename: {}'.format(note_name)})
        messages.append({'role':'user', 'content': 'ENTITY: {}'.format(entity)})
        messages.append({'role':'user', 'content': GRAPH_MSG})
        #messages.append({'role':'assistant', 'content':'Relationships:'})

        chat.printMessages(messages)

        print("Estimated Tokens: {}".format(chat.tizer.calculate_tokens_from_messages(messages)))
        print("Estimated Price: {:.2f}".format(chat.tizer.calculate_price_from_messages(messages)))

        reply = chat.passMessagesGetReply(messages)

        print("Reply")
        print(reply)
        input()

def dict_to_str(dct):
    s = ""

    for header in dct:
        s += header + '\n'

        for v in dct[header]:
            s += '\t- {}\n'.format(v)
        s += '\n'

    return(s)


def notepath_to_name(notepath):
    return(notepath.split('/')[-1])

def hash_check(notepath, table, conn):
    note = open(notepath, 'r')
    notedoc = note.read()
    hash = calc_hash(notedoc)

    db_hash = get_hash_from_table(notepath, notepath_to_name(notepath), table, conn)

    if(db_hash):
        if(db_hash != hash):
            print("HASH MISMASH")
            exit()

            # TO DO: Figure out why the hash don't match 

    print("Updating hash from {} -> {}".format(db_hash, hash))
    update_hash(notepath, notepath_to_name(notepath), table, conn, hash)
    return()


def build_entities(processed_note_dict):
    entities = []

    for category in processed_note_dict:
        print("CATEGORY: {}".format(category))
        for entity in processed_note_dict[category]:
            print("ENTITY: {}".format(entity))
            input()
            if(not entity in entities):
                entities.append(entity)

    return(entities)


def jaccard_distance(list_of_strings, input_string, get_word_set=None):

    if(not get_word_set):
        def get_word_set(string):
            # Helper function to convert a string into a set of words
            return set(string.split())

    input_word_set = get_word_set(input_string)
    distances = []

    for string in list_of_strings:
        string_word_set = get_word_set(string)
        intersection = len(input_word_set.intersection(string_word_set))
        union = len(input_word_set.union(string_word_set))
        jaccard_distance = 1.0 - intersection / union
        distances.append(jaccard_distance)

    return distances

def deobfuscate_entity_list(entity_list, model='gpt-3.5-turbo'):
    explanation = """
Above you see information containing:

```
- Entity 1
- Entity 2
- ...
- Entity n
```

First task : Remove any non NAMED ENTITIES 
"""

    explanation1 = """
Above you see the previous entity list with all non NAMED ENTITIES removed.

Second Task: Remove anything that is an ACTION DESCRIPTION.
"""

    explanation2 = """
Above you see the previous entity list with all ACTION DESCRIPTIONs removed. 

Third Task: Split up anything too long and descriptive. 
"""

    explanation3 = """
Above you see a nearly finished entity list.

Fourth Task: Group the given terms into categories. 
"""


    """
    Return the following information: 

    ```
    Entity Deobfuscation 1: 
    - Entity Variation 1
    - Entity Variation 2
    - ...
    - Entity Variation n

    Entity Deobfuscation 2: 
    ...
    ```
    """
    
    chat = Chatter(model)

    entities_str = '\n'.join(entity_list)

    messages = [] 
    messages.append(chat.getSysMsg('You are DeobfuscateGPT'))
    messages.append(chat.getUsrMsg('CONTEXT - Entities'))
    messages.append(chat.getUsrMsg(entities_str))

    messages.append(chat.getUsrMsg(explanation))

    #print("Passing to CHAT GPT>..............")
    #chat.printMessages(messages)

    reply = chat.passMessagesGetReply(messages)

    #reply_list = reply.split('\n')
    #reply_list = [i for i in reply_list if len(i)]

    messages.append(chat.getAssMsg(reply))
    messages.append(chat.getUsrMsg(explanation1))

    reply = chat.passMessagesGetReply(messages)

    messages.append(chat.getAssMsg(reply))
    messages.append(chat.getUsrMsg(explanation2))

    reply = chat.passMessagesGetReply(messages)

    messages.append(chat.getAssMsg(reply))
    messages.append(chat.getUsrMsg(explanation3))

    reply = chat.passMessagesGetReply(messages)

    messages.append(chat.getAssMsg(reply))

    chat.printMessages(messages)
    input()



    #deobfuscated_dict = process_reply(reply)

    #for d in deobfuscated_dict:
    #    print('D: {}'.format(d))
    #    for dd in deobfuscated_dict[d]:
    #        print("- {}".format(dd))

    #return(deobfuscated_dict)

def build_relationships_for_entity(notepath, notename, model, deobfus, entity_obfusc, tokenlim, clean, stopword, lag, lead):
    setup = """
You should use the note snippet + note name above. 

Your task is to report all relevant relationships between the 'deobfuscated entity' above that you find in the notes.

The relationships should follow the Wikipedia schema type.
The output of a relationship should be in a form of a quad Head, Relationship, Tail, (metadata)
#Peter, WORKS_AT, Hospital (St.Mary's Medical)/n

An example "St. Peter is located in Paris" should have an output with the following format

relationships
St.Peter, LOCATED_IN, Paris\n
"""
    
    chat = Chatter(model)

    script = Scripter()
    script.loadTokenizer(model)
    
    df = script.loadTxt(notepath)
    if(clean):
        df = script.cleanDFPipe(df, stopword=stopword)

    line_list = df['text'].to_list()

    final_replies = [] 
    all_reply = {}
    for i,j in script.getAllTokenChunkBounds(df, tokenlim):
        i = max(0, i-lag)
        j = min(len(line_list), j+lead)

        lines = line_list[i:j]

        messages = []

        messages.append({"role":"system", "content":SYSTEM_MSG})
        messages.append({'role':'user', 'content':'CONTEXT - Note Snippet:'})
        messages.append({'role':'user', 'content':"```" + "\n".join(lines) + "```"})
        messages.append({'role':'user', 'content':'For extra content, the file name of this note is: {}'.format(notename)})
        
        messages.append(chat.getUsrMsg('CONTEXT - Deobfuscated Entity: {}'.format(deobfus)))
        messages.append(chat.getUsrMsg('CONTEXT - Obfuscated Variations: {}'.format("| ".join(entity_obfusc))))
        messages.append({'role':'user', 'content':setup})

        chat.printMessages(messages)
        input()

        #reply = chat.passMessagesGetReply(messages)
        #processed_reply = process_reply(reply)

        #inal_replies.append(reply)
        #all_reply = combine_processed_reply(all_reply, processed_reply)


    save_dict_to_json(all_reply, os.path.join(notepath.split('/')[:-1], notename + '.json'))
    return()




def main():
    parser = make_parser() 
    args = parser.parse_args() 

    if(not args.note or not os.path.exists(args.note)):
        exit()

    #connection = make_connection(args.host, args.database, args.user, args.password)

    #if(not connection):
    #    exit()

    """
    hash_check()
    """

    notename = args.note.split("/")[-1]
    notename = notename.split(".")[0]

    print("LOOKING AT {}".format(notename))

    categories_and_entities_dict = scrape_note_for_categories_and_entities(args.note, notename, args.model, args.tokenlim, args.clean, args.stopword, args.lag, args.lead)
    #categories_and_entities_dict = json.load(open('./notes/{}.json'.format(notename)))

    all_entities = []
    for c in categories_and_entities_dict:
        c_entities = categories_and_entities_dict[c]
        all_entities += [i for i in c_entities if i not in all_entities and len(i)]

    """
    input()
    all_entities = sorted(all_entities)
    tol = 30
    all_entities = [i for i in all_entities if len(i) < tol]
    for i in range(len(all_entities)):
        indices = [j for j in range(len(all_entities)) if j != i]

        strings = [all_entities[j] for j in indices]
        dist = jaccard_distance(strings, all_entities[i])
        vals = [(dist[j], strings[j]) for j in range(len(strings))]
        #vals = sorted(vals, key=lambda x : x[0])[:10]


        tol = 24
        #strings = [i for i in strings if len(i)]
        dist1 = jaccard_distance(strings, all_entities[i], get_word_set=lambda x: set(x))
        vals1 = [(dist1[j], strings[j]) for j in range(len(strings))]
        #vals1 = sorted(vals1, key=lambda x : x[0])[:10]

        vals = [(vals[i][0], vals1[i][0], strings[i]) for i in range(len(vals))]
        vals = sorted(vals, key=lambda x : x[0])[:10]

        print('KEY: {} ({})'.format(all_entities[i], len(all_entities[i])))

        if(vals[0][0] < 1):
            for v, v1, e in vals:
                if(v1 == 1 or v == 1):
                    continue 
                print("  -{} (Word: {:.4f} | Char: {:.4f})".format(e, v, v1))
        else:
            print("   -No Match")
        input()

    input()

    all_entities = sorted(all_entities)
    for i, entity in enumerate(all_entities):
        print(i, ':', entity)

    tol = 22
    for i, entity in enumerate([i for i in all_entities if len(i)<tol]):
        print(i, ':', entity)


    input()
    """

    #deobfuscated_caed = deobfuscate_categories_and_entities_dict(categories_and_entities_dict, 'gpt-3.5-turbo')
    deobfuscated_entities = deobfuscate_entity_list(all_entities, 'gpt-3.5-turbo')
    #save_dict_to_json(deobfuscated_caed, './notes/{}_deobfus.json'.format(notename))

    entity_relationships = {}
    for entity in deobfuscated_caed:
        relationships_for_entity = build_relationships_for_entity(args.note, notename, args.model, entity, deobfuscated_caed[entity], args.tokenlim, args.clean, args.stopword, args.lag, args.lead)

    #entities = build_entities(processed_note_dict)

    #for e in entities:
    #    print(entities)
    #    input()

    #build_entries = build_entries_from_tagged_categories(category_with_tags, args.note, 'gpt-3.5-turbo-16k', args.clean, args.stopword)
    #build_entries = build_entries_from_tagged_categories(category_with_tags, args.note, 'gpt-4', args.clean, args.stopword)

    #entries = build_entries_from_entities(entities, args.note, 'gpt-3.5-turbo-16k', args.clean, args.stopword)



if __name__ == '__main__':
    main()
