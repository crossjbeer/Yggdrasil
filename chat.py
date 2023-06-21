import openai
import os 
import argparse 
import pinecone 
import pandas as pd 

from chatter import Colorcodes, Chatter

openai.api_key = os.getenv('OPENAI_AUTH')

# Alternatively just set your own api key (just don't upload to git!)
pinecone.init(api_key = '27f2b80f-96a2-4c4f-baba-262615e29ac2', environment='asia-southeast1-gcp-free')

INDEX = pinecone.Index('ygg')
COLORCODE = Colorcodes()

def embeddingToText(path):
    res = pd.read_csv(path, header=0)

    return({res['index'].values[i] : res['text'].values[i] for i in range(len(res))})

def estimateTokens(s, charPerToken = 4):
    return(len(s) / charPerToken)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-q', '--query', help='Query for Chat GPT', type=str, default=None, required=False)
    parser.add_argument('-m', '--model', help='Open AI model to use [gpt3.5-turbo, gpt4]', type=str, default='gpt-4')
    parser.add_argument('-n', '--nvector', help='Number of vectors to query', type=int, default=25)
    parser.add_argument('-p', '--path', type=str, help='Path to directory containing <date> folders with embedding files...')

    args = parser.parse_args() 

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
        include_values=True
    )
    print(f"{COLORCODE.orange}Pinecone Query Complete{COLORCODE.reset}\n")

    relatedID = [i['id'] for i in relatedVectors['matches']]

    sessionToID = {}
    for id in relatedID:
        session, _, _, bs, stride, index = id.split("_")

        index = int(index)

        sessionCode = session + "_" + bs + "_" + stride

        if(sessionCode in sessionToID): 
            sessionToID[sessionCode].append(index)
        else:
            sessionToID[sessionCode] = [index]

    sessionToIndexToText = {} 
    for session in sessionToID:
        session_date, bs, stride = session.split("_")

        sessionToIndexToText[session] = embeddingToText(os.path.join(args.path, session_date, "{}_{}.csv".format(bs, stride)))
        

    sessionToText = {}
    for session in sorted(list(sessionToID.keys())):
        session_date, bs, stride = session.split("_")

        bs = int(bs[2:])
        stride = int(stride[3:])

        sessionToText[session] = ""

        if(len(sessionToID[session]) <= 1):
            #print("SESSION TO ID: {}".format(sessionToID[session]))
            sessionToText[session] = sessionToIndexToText[session][sessionToID[session][0]]
            #print("STT:")
            #print(sessionToText[session])

        else:
            for i in range(len(sessionToID[session])-1):
                currentInd = sorted(sessionToID[session])[i]
                nextInd    = sorted(sessionToID[session])[i+1]

                if(nextInd - currentInd < bs): #If the difference between indices is < the batch, we know there must be (some) overlap, so we should account for that...
                    howMuchOverlap = nextInd - currentInd

                    currentText = sessionToIndexToText[session][currentInd]
                    currentLines = currentText.split("\n")

                    sessionToText[session] += "\n".join(currentLines[:howMuchOverlap])

                else:
                    sessionToText[session] += sessionToIndexToText[session][currentInd] + '\n'

            sessionToText[session] += sessionToIndexToText[session][sorted(sessionToID[session])[-1]]


    allText = "\n".join(sessionToText[i] for i in sessionToText)


    #print("Querying OpenAI using {} | {} Tokens...".format(args.model, estimateTokens(allText)))
    """
    response = openai.ChatCompletion.create(
        model=args.model,
        messages = [
            {'role':'system', 'content':'You are a Dungeons and Dragons AI'},
            {'role':'user', 'content':'Below is a query provided by the user. You should use the information provided further down to answer this query as well as possible.'},
            {'role':'user', 'content': args.query},
            {'role':'user', 'content': 'Below is the context provided. You will see a text transcript of a dungeons and dragons campaign. Each line is labeled with a speaker. Here are the speaker codes, names, and character / role:\n1) cro: Crossland (DM)\n2) let: Leticia (Russet Crow)\n3) ric: Richard (Likkvorn)\n4) sim: Simon (Lief) 5) ben: Ben (Oskar) 6) kacie: Kacie (Isra). Please read through what was said, and help with the query as best you can.'},
            {'role':'user', 'content':allText}
        ]
    )
    """
    messages = [
            {'role':'system', 'content':'You are a Dungeons and Dragons AI'},
            {'role':'user', 'content':'Below is a query provided by the user. You should use the information provided further down to answer this query as well as possible.'},
            #{'role':'user', 'content': args.query},]
            {'role':'user', 'content':prompt},
            {'role':'user', 'content': 'Below is the context provided. You will see a text transcript of a dungeons and dragons campaign. Each line is labeled with a speaker. Here are the speaker codes, names, and character / role:\n1) cro: Crossland (DM)\n2) let: Leticia (Russet Crow)\n3) ric: Richard (Likkvorn)\n4) sim: Simon (Lief) 5) ben: Ben (Oskar) 6) kacie: Kacie (Isra). Please read through what was said, and help with the query as best you can.'},
        ]
    
    chat = Chatter(args.model)
    chat.chat(allText, True, messages)

    #print("\n\n\n~~~ Chat GPT Says ~~~")
    #print(response['choices'][0]['message']['content'])
    

if (__name__ == "__main__"):
    main()