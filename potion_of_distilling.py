"""
We will use this script to get the important information out of a document. 
We will restructure the document into a series of smaller, concentrated documents, using GPT. 
"""

import os 
import argparse

from chatter import Chatter 
from scripter import Scripter
from parsers import parser_gpt, parser_sql, valid_path, valid_path_build


DISTILLER = """You are now operating as 'DistillGPT,' a specialized assistant designed to help break down and distill information from poorly structured documents. 
Your primary goal is to extract key points, organize them into a structured bulleted list, and provide information in a concise and clear format.

Instructions:
- Given a document chunk, identify main ideas or key points.
- Organize the information in a bulleted list for clarity.
- Include relevant details and subpoints where necessary.
- Aim for conciseness while capturing essential information.

Use the provided prompt for guidance and repeat the process for each document chunk. Your objective is to distill the document into a more usable and organized form.

Now, let's get started! Please proceed with the provided prompt and help distill the information.
"""

DOC_MASTER = """You are now operating as the DOC MASTER. 
You are a world class clerical worker, and you have been tasked with organizing information from a document into a series of smaller documents.
Your job is to organize INFORMATION from a DOCUMENT into CATEGORIES and FILES. 

You will provided with a DOCUMENT, this is the name of some document.
You will also be provided with a chunk of INFORMATION from the DOCUMENT.
You may also be given a USER PROMPT, which usually contains details about the DOCUMENT. 
You will also be provided with a list of FILES. If none are provided, you can assume there are no files yet. 
Each file name should describe some category of information from the document. 

Thinking in steps, organize the INFORMATION into categories. 
Categories can be broad. We want to concentrate relevant information into valuable files.

For each of your categories, determine which FILE it should be stored in. 
If the category does not fit into any of the FILES, create a new FILE.
New files should be all lowercase and use underscores instead of spaces. They should all end in .txt. 
Files should also be fairly simple, and should describe the category of information they contain.

Next, determine which CATEGORY the INFORMATION should be stored under.
Categories should be all lowercase and use underscores instead of spaces.

Finally, write the INFORMATION under the CATEGORY.
Please be sure to include all relevant information.
Please also run a spell check and formatting check on the information before storing it. We are trying to distill the information into a more usable and organized form, while not eliminating anything crucial.

Structure your response as follows: 
File: <FILE NAME>
Category: <CATEGORY NAME>
Information: 
<INFORMATION>

Now please take a deep breath, and let's get started!
"""

INFO_MASTER = """You are now operating as the INFO MASTER.
Your job is to add INFORMATION to a FILE under a CATEGORY. 

You will be provided with a FILE NAME, list of CATEGORIES, a suggested category, and a chunk of INFORMATION.
You may also be provided with a USER PROMPT, which usually contains details about the all this information is from. 

Thinking in steps, determine which CATEGORY the INFORMATION should be stored under.
If the suggested category is correct, you may use that.
If the suggested category is incorrect, you may use one of the other categories.
If none of the categories are correct, you may create a new category.

Structure your response as follows:
Category: <CATEGORY NAME>

Now please take a deep breath, and let's get started!
"""


def make_parser():
    parser = argparse.ArgumentParser(description='Distill a document into a series of smaller documents')

    parser.add_argument('path', help='Path to the document to distill', type=valid_path)
    parser.add_argument('--token_lim', help='Number of tokens for each step (Default: 1000)', type=int, default=1000)
    parser.add_argument('--save_dir', help='Directory to save the distilled documents (Default: ./doc_master)', type=valid_path_build, default='./doc_master')

    parser = parser_gpt(parser)
    parser = parser_sql(parser)

    return(parser)

def distill_step(text, chatter, distiller=DISTILLER):
    """
    Distill a single step of the document. 
    """
    # Get the prompt 

    messages = []
    messages.append(chatter.getSysMsg(distiller))
    messages.append(chatter.getUsrMsg(text))

    #reply = chatter.passMessagesGetReply(messages)
    reply = chatter(messages)

    #chatter.printMessages(messages+[chatter.getAssMsg(reply)])
    #input()

    return(reply)

def parse_doc_master(reply):
    """
    Parse the reply from the doc master. 
    """
    # Split the reply into lines
    reply_lines = reply.split('\n')

    # Initialize variables to store the current block and all blocks
    current_block = {}
    all_blocks = []
    line_block = []
    # Iterate over the lines
    for line in reply_lines:
        # If the line starts with 'File', start a new block
        if line.startswith('File'):
            if current_block:
                # If there is a current block, add it to all blocks
                current_block['information'] = line_block
                all_blocks.append(current_block)
            # Start a new block
            current_block = {'file': line.split(': ')[-1]}
        elif line.startswith('Category'):
            # Add the category to the current block
            current_block['category'] = line.split(': ')[-1]
        elif line.startswith('Information'):
            line_block = [] 
            line_block.append(line.split(": ")[-1])
        else:
            line_block.append(line)

    # Add the last block to all blocks
    if current_block:
        current_block['information'] = line_block
        all_blocks.append(current_block)

    # Convert the information lists to strings
    for block in all_blocks:
        block['information'] = '\n'.join(block['information'])

    # Error handling: Check that each block has 'file', 'category', and 'information'
    for block in all_blocks:
        if 'file' not in block or 'category' not in block or 'information' not in block:
            raise ValueError("Invalid block format. Each block should have 'file', 'category', and 'information'.")

    return all_blocks

def doc_master_step(text, chatter, file_dir, doc_name, user_context=None, doc_master=DOC_MASTER, *args, **kwargs):
    """
    Distill a single step of the document. 
    """
    # Get available files: 
    files = os.listdir(file_dir)
    files = [f for f in files if f.endswith('.txt')]

    messages = []
    messages.append(chatter.getSysMsg(doc_master))
    messages.append(chatter.getUsrMsg(f'DOCUMENT:\n{doc_name}'))
    messages.append(chatter.getUsrMsg(f'INFORMATION:\n{text}'))
    messages.append(chatter.getUsrMsg(f"""FILES:\n{" ".join(files)}"""))

    if(user_context is not None):
        messages.append(chatter.getUsrMsg(f'USER PROMPT: {user_context}'))

    reply = chatter(messages)
    for block in parse_doc_master(reply):
        file = block['file']
        category = block['category']
        information = block['information']

        print(f"FILE: {file}")
        print(f"CATEGORY: {category}")
        print(f"INFORMATION:\n{information}")

        if(file not in files):
            print(f"Creating file {file}")
            with open(os.path.join(file_dir, file), 'w') as wf: 
                wf.write(f"Category: {category}\n")
                wf.write(information)

        elif file in files: 
            print(f"Appending to file {file}")
            info_master_step(information, category, os.path.join(file_dir, file), chatter, user_context=user_context, info_master=INFO_MASTER)
        print("**\n")

    return(reply)


def info_master_step(information, category, path, chatter, user_context=None, info_master=INFO_MASTER, *args, **kwargs):
    """
    Query Info Master to append information to a file under a category. 
    """

    scripter = Scripter() 
    df = scripter.loadTxt(path)
    categories = scripter.parseCategoriesFromInfoDoc(df)

    if(df is None):
        exit('Unable to load [{}]'.format(path))

    messages = []
    messages.append(chatter.getSysMsg(info_master))
    messages.append(chatter.getUsrMsg(f"FILE NAME: {path.split('/')[-1]}"))
    messages.append(chatter.getUsrMsg(f"CATEGORIES: {' '.join(categories)}"))
    messages.append(chatter.getUsrMsg(f"SUGGESTED CATEGORY: {category}"))
    messages.append(chatter.getUsrMsg(f"INFORMATION:\n{information}"))

    if(user_context is not None):
        messages.append(chatter.getUsrMsg(f'USER PROMPT: {user_context}'))

    reply = chatter(messages)
    reply_category = reply.split(": ")[-1]

    scripter = Scripter()
    df = scripter.loadTxt(path)
    categories = scripter.parseCategoriesAndInfoFromInfoDoc(df)

    print("[IM] Categories: {} | Reply Category: {}".format(categories, reply_category))
    if(reply_category in categories):
        categories[reply_category].append(information)
    else:
        categories[reply_category] = [information]

    with open(path, 'w') as wf:
        for category, info in categories.items():
            wf.write(f"Category: {category}\n")
            for i in info:
                wf.write(i+'\n')

    return(reply)


def distill(path, model, token_lim, save_dir, query, *args, **kwargs):
    """
    Distill a document into a series of smaller documents. 
    """

    # Initialize the chatter 
    chatter = Chatter(model=model)

    # Initialize the scripter 
    scripter = Scripter()
    scripter.loadTokenizer('ada-002')
    df = scripter.loadTxt(path)
    print(df)

    token_bounds = scripter.getAllTokenChunkBounds(df, token_lim)

    doc_master_dir = f"./{save_dir}/{path.split('/')[-1]}"
    if(not os.path.exists(doc_master_dir)):
        os.makedirs(doc_master_dir)

    # Get the text for each chunk
    inpy = ''
    for i, (start, end) in enumerate(token_bounds):
        print(f'Processing chunk {i+1} of {len(token_bounds)}')
        chunk = df[start:end]
        text = scripter.getText(chunk)

        reply = doc_master_step(text, chatter, doc_master_dir, path.split('/')[-1], doc_master=DOC_MASTER, user_context=query)

        if(inpy != 'l'):
            inpy = input('Press l to loop. q to quit. ')
        if(reply == 'q'):
            break





def main():
    parser = make_parser() 
    args = parser.parse_args()

    distill(**vars(args))

if(__name__ == "__main__"):
    main()