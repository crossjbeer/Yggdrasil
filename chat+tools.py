import openai
import os 
import argparse 
import pinecone 
import numpy as np 
from pydantic import BaseModel, Field


#from langchain import LLMChain
#from langchain.chains import ChatVectorDBChain
from langchain.chat_models import ChatOpenAI

from prompts import tool_chat_system, tool_query, lore_master

from langchain.prompts import PromptTemplate
from langchain.prompts import ChatPromptTemplate
from langchain.prompts.chat import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatMessagePromptTemplate
from langchain.output_parsers import PydanticOutputParser

from chatter import Colorcodes, Chatter
from scripter import Scripter, NAMEDICT


os.environ['OPENAI_API_KEY'] = os.getenv("OPENAI_AUTH")

# Alternatively just set your own api key (just don't upload to git!)
pinecone.init(api_key = os.getenv('PINECONE_AUTH'), environment='asia-southeast1-gcp-free')


def make_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-q', '--query', help='Query for Chat GPT', type=str, default=None, required=False)
    parser.add_argument('-m', '--model', help='Open AI model to use [gpt3.5-turbo, gpt4]', type=str, default='gpt-4')
    parser.add_argument('-n', '--nvector', help='Number of vectors to query', type=int, default=5)
    parser.add_argument('--host', help='Database host', type=str, default='localhost')
    parser.add_argument('--user', help='Database user', type=str, default='ygg')
    parser.add_argument('--db', help='Database name', type=str, default='yggdrasil')
    parser.add_argument('--password', help='Database password', type=str, default='ygg')
    parser.add_argument('--table', help='Table with Transcriptions', default='transcript', type=str)
    parser.add_argument('--clean', help='Clean text to anonymized and stripped', action='store_true')

    parser.add_argument('--stopwords', help='Eliminate stopwords from transcript', action='store_true')
    parser.add_argument('--dbtype', type=str, help='Type of database to run', default='postgresql')
    parser.add_argument('--pinecone_namespace', type=str, help='Pinecone DB Namespace to use.', default='')
    parser.add_argument("--pinecone_index", type=str, help='Pinecone DB Index to use', default='yggy')

    return(parser)


TOOLS = {"Note Index":"Lookup DND Campaign Notes related to Query",
         #"Rules Index":"Lookup DND Rules related to Query",
         "Session Transcript Index":"Lookup DND Session Transcriptions related to Query"
         }

def makeToolStr(tools):
    tool_str = ""
    for i, t in enumerate(tools):
        tool_str += "({}) {} - {}\n".format(i+1, t, tools[t])

    return(tool_str)

class RankingFormat(BaseModel):
    tool_list: list = Field(description="list of ranked tools")

def rankToolsBasedOnQuery(query, tools=TOOLS):
    tool_str = makeToolStr(tools)

    parse = True
    if(parse):
        global tool_query
        tool_query += '\n{format_instructions}'

    chat_template = ChatPromptTemplate.from_messages(
        [
            SystemMessagePromptTemplate.from_template(tool_chat_system),
            HumanMessagePromptTemplate.from_template(tool_query)
        ]
    )

    llm = ChatOpenAI(model='gpt-4')
    parser = PydanticOutputParser(pydantic_object=RankingFormat)
    if(parse):
        #print(chat_template.format_messages(query=query, tool_str=tool_str, format_instructions=parser.get_format_instructions()))
        msgs = chat_template.format_messages(query=query, tool_str=tool_str, format_instructions=parser.get_format_instructions())
        for msg in msgs:
            print(msg.content)
        
        msg = llm(chat_template.format_messages(query=query, tool_str=tool_str, format_instructions=parser.get_format_instructions()))
        
    else:
        msg = llm(chat_template.format_messages(query=query, tool_str=tool_str))

    print(msg)
    input()

    data = parser.parse(msg.content)
    return(data.tool_list)


def getQueryEmbedding(query):
    col = Colorcodes()

    print(col.pred("Converting query into Embedding..."))
    response = openai.Embedding.create(
            input=query,
            model='text-embedding-ada-002'
    )
    embeddings = response['data'][0]['embedding']
    print(col.porange("Embedding Complete"))

    return(embeddings)

def queryPineconeForRelatedVectors(embedding, nvec, pinecone_namespace, pinecone_index='yggy'):
    index = pinecone.Index(pinecone_index)

    col = Colorcodes()

    print(col.pred("Using Embedding to Query Pinecone for top {args.nvector} Vectors..."))
    relatedVectors = index.query(
        top_k=nvec,
        vector=[embedding] ,
        include_values=True, 
        namespace=pinecone_namespace
    )
    print(col.porange("Pinecone Query Complete"))

    return(relatedVectors)

def relatedVectorToIDInfo(relatedVectors):
    relatedID = [i['id'] for i in relatedVectors['matches']]
    filename = []
    id = [] 
    batchsize = [] 
    for rid in relatedID:
        print("ID {}".format(rid))
        fn, sid, bs = rid.split("_")

        filename.append(fn[1:-1])
        id.append(int(sid))
        batchsize.append(int(bs))

    return(filename, id, batchsize)

def relatedVectorToInterval(relatedVectors):
    filename, id, batchsize = relatedVectorToIDInfo(relatedVectors)

    unique_notes = np.unique(filename)
    noteToInterval = {}
    
    for s in unique_notes:
        indices = [id[i] for i in range(len(id)) if filename[i] == s]
        #bs      = [batchsize[i] for i in range(len(id)) if filename[i] == s]

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

    return(noteToInterval)

def intervalsToText(idToInterval, table, connection, script, clean, stopwords):
    #allText = ""
    #cursor = connection.cursor()

    """for session in idToInterval:
        c_query = idToInterval[session]

        #total_lines_query = f"SELECT COUNT(*) FROM {table} WHERE session = %s;"
        #cursor.execute(total_lines_query, (session,))
        #row_count = cursor.fetchone()[0]

        for start, end in c_query:
            print("[{}] Pulling Lines {} -> {}".format(session, start, end))
            #display_percentage_range(int(100*(end/row_count)),int(100*(start/row_count)))
            #query = f"SELECT class, text FROM {table} WHERE session = %s AND session_id > %s AND session_id < %s ORDER BY session_id ASC;"

            cursor.execute(query, (session, start, end))

            rows = cursor.fetchall()
            str_rows = []
            for row in rows:
                c = row[0]
                text = row[1]

                if(clean):
                    text = script.cleanText(t, stopword = stopwords)
                text = f"{NAMEDICT[c]}: {text}" if c in NAMEDICT else 'None'
                str_rows.append(text)

            allText += "\n"
            allText += "\n".join(str_rows)
            """
    
    allText = ""
    for note in idToInterval:
        allText += "***\n{}\n***\n".format(note)

        c_script = Scripter()
        c_df = c_script.loadTxt('./notes/{}.txt'.format(note))

        for start, end in idToInterval[note]:
            c_str = c_script.getStrRows(c_df, start, end-start)
            allText += "\n".join(c_str) + "\n"
    return(allText)


def pinecone_notes(args, query, script, pinecone_index):
    embedding = getQueryEmbedding(query)

    relatedVectors = queryPineconeForRelatedVectors(embedding, args.nvector, 'notes', pinecone_index)

    intervals = relatedVectorToInterval(relatedVectors)

    text = intervalsToText(intervals, args.table, script.connection, script, args.clean, args.stopwords)

    return(text)


def relatedVectorToSessionText(relatedVectors, table, script, clean, stopwords):
    cursor = script.connection.cursor() 

    relatedID = [i['id'] for i in relatedVectors['matches']]
    sessions = []
    session_names = []
    session_id = []
    whispers = []
    batchsize = [] 

    for id in relatedID:
        print("ID {}".format(id))
        s, sn, w, sid, bs = id.split("_")

        sessions.append(s)
        session_names.append(sn)
        session_id.append(int(sid))
        whispers.append(w)
        batchsize.append(int(bs))

    unique_sessions = np.unique(sessions)
    sessionToQuery = {}
    
    for s in unique_sessions:
        indices = [session_id[i] for i in range(len(session_id)) if sessions[i] == s]
        bs      = [batchsize[i] for i in range(len(session_id)) if sessions[i] == s]
        whisp   = [whispers[i] for i in range(len(session_id)) if sessions[i] == s]

        if(len(indices) == 1):
            sessionToQuery[s] = [(indices[0], indices[0] + bs[0])]
            continue

        bs = [x for _, x in sorted(zip(indices, bs))]
        whisp = [x for _, x in sorted(zip(indices, whisp))]
        indices = sorted(indices)

        #for i in range(len(indices)):
        #    if(whisp[i] != args.whisper)

        querys = [] 
        i = 0 
        start_ind = None 
        while i < len(indices)-1:#
            cind, nind = indices[i], indices[i+1]
            cb, nb = bs[i], bs[i+1]

            #if(whisp[i] !=  )

            if(not start_ind):
                start_ind = cind 

            if(cind + cb <= nind):
                querys.append((start_ind, cind+cb))
                start_ind = None 
                i += 1
            
            else:
                indices[i] = nind
                bs[i] = nb 

                indices.pop(1)
                bs.pop(1)

        if(start_ind is not None):
            querys.append((cind, indices[-1] + bs[-1]))
        else:
            querys.append((indices[-1], indices[-1] + bs[-1]))
        sessionToQuery[s] = querys

    allText = ""
    for session in sessionToQuery:
        c_query = sessionToQuery[session]

        total_lines_query = f"SELECT COUNT(*) FROM {table} WHERE session = %s;"
        cursor.execute(total_lines_query, (session,))
        row_count = cursor.fetchone()[0]

        for start, end in c_query:
            print("[{}] Pulling Lines {} -> {}\nPart of Doc:".format(session, start, end))
            #display_percentage_range(int(100*(end/row_count)),int(100*(start/row_count)))
            query = f"SELECT class, text FROM {table} WHERE session = %s AND session_id > %s AND session_id < %s ORDER BY session_id ASC;"

            cursor.execute(query, (session, start, end))

            rows = cursor.fetchall()
            str_rows = []
            for row in rows:
                c = row[0]
                text = row[1]

                if(clean):
                    text = script.cleanText(t, stopword = stopwords)
                text = f"{NAMEDICT[c]}: {text}" if c in NAMEDICT else 'None'
                str_rows.append(text)

            allText += "\n"
            allText += "\n".join(str_rows)

    return(allText)


def pinecone_session(args, query, script, pinecone_index):
    embedding = getQueryEmbedding(query)

    relatedVectors = queryPineconeForRelatedVectors(embedding, args.nvector, 'session', pinecone_index)

    sessionText = relatedVectorToSessionText(relatedVectors, args.table, script, args.clean, args.stopwords)

    return(sessionText)
    


def queryWithToolText(query, orderedTools, toolToText, model):
    chat = Chatter(model)

    allText = ""
    for i, tool in enumerate(orderedTools):
        allText += 'Tool {}: {}'.format(i, tool)
        allText += 'Response {}: ```{}```'.format(i, toolToText[tool])
    
    messages = [
        chat.getSysMsg(lore_master),
        chat.getUsrMsg(f'My Query: {query}'),
        chat.getUsrMsg(allText),
        chat.getUsrMsg(f"My Query: {query}")
    ]

    chat.printMessages(messages)
    input()

    response = chat.passMessagesGetReply(messages)

    return(response)



def toolChat(args, script, **kwargs):
    col = Colorcodes()

    query = args.query 
    if(not query or not len(query)):
        query = input(col.pblue('Prompt> '))
        print() 

    ranking = rankToolsBasedOnQuery(query)

    print("Ranking: {}".format(ranking))

    toolToText = {} 
    for tool in ranking:
        if(tool == 'Note Index'):
            text = pinecone_notes(args, query, script, args.pinecone_index)
        elif(tool == 'Session Transcript Index'):
            text = pinecone_session(args, query, script, args.pinecone_index)
        elif(tool == 'Rules Index'):
            pass
            #pinecone(args, query, script, 'phb', args.pinecone_index)

        toolToText[tool] = text 

    for t in toolToText:
        print(t)
        print(toolToText[t])
        input()

    response = queryWithToolText(query, ranking, toolToText, args.model)

    print(col.pblue(response))
    return()

    





def main():
    parser = make_parser()
    args = parser.parse_args() 

    script = Scripter() 
    col    = Colorcodes()

    dbtype = args.dbtype.upper()

    if(dbtype == 'POSTGRESQL'):
        script.connectPostgreSQL(args.host, args.db, args.user, args.password)
    elif(dbtype == 'MYSQL'):
        script.connectMySQL(args.host, args.db, args.user, args.password)

    if(not script.connection):
        print(col.porange(f'Cannot connect to {args.dbtype} Database...'))
        exit()

    toolChat(args, script)

    

    
    




if __name__ == "__main__":
    main() 