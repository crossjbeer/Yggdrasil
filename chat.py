import openai
import os 
import argparse 
import pinecone 
import psycopg2
import pandas as pd 
import numpy as np 

from chatter import Colorcodes, Chatter
from scripter import Scripter, NAMEDICT

openai.api_key = os.getenv('OPENAI_AUTH')

# Alternatively just set your own api key (just don't upload to git!)
pinecone.init(api_key = os.getenv('PINECONE_AUTH'), environment='asia-southeast1-gcp-free')

INDEX = pinecone.Index('yggy')
COLORCODE = Colorcodes()

def main():
    messages = [{'role':'system', 'content':"""You are the Lore Master. You preside over the sacred transcript of a dungeons and dragons campaign.
        Your job is to be the ultimate dnd assistant. The user may ask you any variety of questions related to dungeons and dragons. 
        This can include asking to help build a village, design a character, assist with roleplay, or produce writing materials. 

        You will be provided with a section of the transcript related to the question the user has asked. Use this transcript and any 
        background knowledge you may have to answer the user's question as well as you can. 

        DO NOT MAKE UP ANYTHING UNLESS SPECIFICALLY ASKED. Use the information provided to answer questions and, if the information is 
        not sufficient, do not resort to making up information. Simply report that no other relevant information was provided.
                 
        Be sure to answer in at least a few paragraphs. Be thorough and give the user the specific detail they are interested in. 
        
        Here are the speaker codes and characters / roles:
        <1> DM
        <2> Likkvorn
        <3> Russet Crow
        <4> Lief
        <5> Oskar
        <6> Isra
        """}]
    

    parser = argparse.ArgumentParser()
    parser.add_argument('-q', '--query', help='Query for Chat GPT', type=str, default=None, required=False)
    parser.add_argument('-m', '--model', help='Open AI model to use [gpt3.5-turbo, gpt4]', type=str, default='gpt-4')
    parser.add_argument('-n', '--nvector', help='Number of vectors to query', type=int, default=5)
    parser.add_argument('--host', help='Database host', type=str, default='localhost')
    parser.add_argument('--user', help='Database user', type=str, default='ygg')
    parser.add_argument('--db', help='Database name', type=str, default='yggdrasil')
    parser.add_argument('--password', help='Database password', type=str, default='ygg')
    parser.add_argument('--table', help='Table with Transcriptions', default='transcript', type=str)
    parser.add_argument('--stopwords', help='Eliminate stopwords from transcript', action='store_true')


    args = parser.parse_args() 


    script = Scripter()
    #script.connectMySQL(args.host, args.db, args.user, args.password)
    script.connectPostgreSQL(args.host, args.db, args.user, args.password)

    if(not script.connection):
        print(f"{COLORCODE.orange}Cannot connect to Database{COLORCODE.reset}\n")
        exit()
    else:
        cursor = script.connection.cursor()

    prompt = args.query
    if(not prompt or not len(prompt)):
        prompt = input(f"{COLORCODE.blue}Prompt> {COLORCODE.reset}")
        print()

    prompt = """Please prepare a description of Russet Crow. This description should cover Russet Crow's appearance, some details about his class and a setting in the world. Please prepare this description as a prompt for use in an image diffusion model. Here are some examples of good prompts, which you should emulate:
    
    1. Centered portrait of an ultra detailed Mechanical Cyberpunk male Android, looking into the camera, intricate, elegant, super highly detailed, smooth, sharp focus, no blur, no dof, extreme illustration, Unreal

2. ﻿enlightend compassionate, empathetic, confident, unique woman made of butterflies and flower petals, scorched beauty portrait, artgerm, peter mohrbacher

3. 1girl, 8k resolution, photorealistic masterpiece by Aaron Horkey and Jeremy Mann, intricately detailed fluid gouache painting by Jean Baptiste, professional photography, natural lighting, volumetric lighting, maximalist, 8k resolution, concept art, intricately detailed, complex, elegant, expansive, fantastical, cover

4. A burger falling in pieces juicy, tasty, hot, promotiona
l photo, intricate details, hdr, cinematic, adobe lightroom, highly detailed

5. ﻿autumn by ashley on doodles, in the style of striking digital surrealism, pointillist dot paintings, feminine beauty, swirling colors, dark bronze, contemporary turkish artConverting query into Embedding...
, digitally enhanced --ar 38:39 --s 750 --v 5. 2

6.﻿ underwater temple, (ancient city of atlantis), high detail, majestic city, dramatic scale, 8k, blue, fish, (coral reef), Greek temple, Greek architecture, godrays, cinematic lighting, concept art, distinct, in the style of studio ghibli

7. Cyberpunk cityscape with towering skyscrapers, neon signs, and flying cars.

8. Digital painting of an astronaut floating in space, with a reflection of Earth in the helmet visor."""

    asdf = """Session Notes - 7/16/23
Players recount their level up: 
Oskar: 
Exploration + magic in the crystals
Had some new ideas
Can now add more infusions. Can infuse armors 
Can also have more simultaneous infusions 
Can also choose an artificer ‘specialization’ 
Choosing the armorer 
Right now, the armor is manifesting after borrowing a shard of crystal from Likkvorn
Wants to shave the crystal down 
Does so successfully
Using the smith’s tools, Oskar embeds the crystals into the gauntlets and inlays them with copper wire
After smacking with the artificer spice, the crystals now glow and shoot the occasional sparks 
Oskar is practicing his gauntlet hit on Likkvorn 
Hits for 2 dmg. The circuit completes. The punch is light and as the copper connects with his chest that energy is released 
Russet: 
Russet would sleep through oskar’s and Likkvorn’s hooliganism 
Russet is going through a transformation in his sleep
He can feel the spells ‘start to work’ more better 
He can fee the magical abilities course through his veins 
Has metamagic: 
Quickened spell
Twin Spell 
Russet is becoming a bit of a damage dealer 
Still doesn’t understand what they can do completely 
Also feeling a link with the pink crystals. First real object they have investigated and with a full archeological history behind. 
Learning a ‘through line’ in the form of this magical energy radiating from the crystals .
Good motivation for russet to investigate more 
Russet awoken from slumber by the gauntlet punch, thinking it is a storm
Russet has also created a little nest in the lofty area of Cliff’s building
Likkvorn:
Learning a lot from encounters in the bridgeman’s house 
Studying the crystals and the floating painting 
Learning how to apply the little gifts he has picked up along the way to other abilities 
Taking inspiration from living under the ground, and a couple tricks from the “Wiley Spider” learning a couple spells like “spider climb” and “web”
Channeling necromancer studies into manipulating life and senses 
Planning to start experimenting with mobility using things like spider climb 
The night before sleep, He is looking at items he was picking up
Getting ready to go: 
Hears thunderous claps in the distance (simon’s character in the distance) 
Cliff and likkvorn make jokes about many thunderous booms as a fart 
Russet crow doesn’t understand why this is a joke, just farts usually 
Russet imagined famous graphic scroll hero “Bronze Dwarf” (Ironman)
Oskar wants to go investigate, as does russet and likkvorn 
Russet considering experimenting with the snagroot 
Cliff insinuates that he will make his son’s middle name something related to the party
Heading towards the center of town:
In the center of barksbreak
See the decaying snagroot
Around the corner, simon’s character continues to thunderclap 
See simon’s character instrumentally preparing a spell, strumming on strings built into their own body
Seeing simon’s character (Melodious) : 
Described as: 
About 6ft tall
Woody in texture, a silvery woody textured body
Built like a soldier 
He has clothes, but he doesn’t want to be wearing clothes 
Glowy blue crystalline eyes 
Party thinking: 
Oskar: What the hell
Russet: This guy is shiny and confusing 
Lik: interested in the strings which are a part of his body
Strings:
Go down the humanoids lats 
“Chelo chested” 
“Dulcimer chested” 
Experimenting with the vine: 
Raked: rake pulled into the vines
Discussing using crystal:
Shake the vial near the snagroot 
Vines move quickly near the snagroot 
Vines are healed with poison and necrotic damage 
Vines are damaged (x2) with healing 
Destroyed 2sqft section w/ healing word 
Rescuing Melodious: 
Likvorn created dollorous bell removing the vines from Melodious’ feet 
Melodious casts thunder clap, pushing the other vines away and jumping from his captivity
Melodious falls to the ground, getting trapped once more
Meeting Melodious: 
Melodious jumps up and says ‘yeehaw’
Asked who he is: 
Replies bonk, yeehaw, bling, boing, strum
Asked how he got here: 
whisper , whisper 
Description:
Obviously not flesh, wood and brass 
 Oskar takes out his artificer goggles to investigate 
Doesn’t do well but has awesome glasses 
Melodious points to the ‘m-p-0’ on his arm
Oskar calls him ‘Empy’
Ask where he was going: 
Points at the party 
Debating on whether to take him
Empy demonstrates his viability by proving he can be a distraction 
Russet asks if empy knew about the party before the day: 
Says yes
Lik asks if he knows nethergloom
Yes
Russet asks if empy has been following:
Yes
Party figures out where empy met them: 
Asks to point to who he has been following longest: points to all 
Figured out they were followed from timberhold
Have Empy if he pinky promises to not harm the party 
Plan:
Considering praying
Considering going to troll + cave 
Considering learning where the vines are coming from 
Considering entering the chieftain’s mansion 
Players in the church: 
Russet tastes the dirt, rolls arcana 
The party puts Liefs shoes and a picked flower in 
Russet gets an ink well from the cloyster in the back
Russet finds and puts on a ragged holy garb 
Lik is conflicted about stealing from the church
Russet is worried about getting tricked into something
Rusest mentions this place feeling like a sanctuary and feels less menacing. Has to be something that gives off the same vibes
Wants some way to bring the power of berronar with us 
Russet fills ink well with dirt 
Lik and Oskar think that the god abandoned this place 
Likkvorn finds a wheat stalk crown behind a set of 3 small bells 


Ringing the bell: 
Oskar + Empy rung the bell
The sng root receded into the noose bloom, recoiling with each ring
The Chieftain's Mansion: 
Searching study:	
Empy finds: 3 records 
Wisp Rock
Swiftblade Jiggy
Meadowkin meadowkin where are you meadowkin 
Oskar found a book on artificing 
Both found the pile belonging to the bullywug 
Bullywug Escapes: 
The bullywug escaped into the mansion bedroom after being seen by the party
The party is rolling to see if they can make out is nat 20 escape 
Oskar finds the word slimefoot written on the ground 
Oskar goes to the balcony, sees the collapsed bridgeman’s house and the bridge across moradin’s sprue 
Oskar sees the slime on the railing, then looks down to see the bullywug creature 
A chase ensues 

!!! Please summarize these session notes in context of the greater campaign, given everything you know about it
"""

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
        namespace='transcript'
    )
    print(f"{COLORCODE.orange}Pinecone Query Complete{COLORCODE.reset}\n")

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

        total_lines_query = f"SELECT COUNT(*) FROM {args.table} WHERE session = %s;"
        cursor.execute(total_lines_query, (session,))
        row_count = cursor.fetchone()[0]

        for start, end in c_query:
            print("[{}] Pulling Lines {} -> {}\nPart of Doc:".format(session, start, end))
            #display_percentage_range(int(100*(end/row_count)),int(100*(start/row_count)))
            query = f"SELECT class, text FROM {args.table} WHERE session = %s AND session_id > %s AND session_id < %s ORDER BY session_id ASC;"

            cursor.execute(query, (session, start, end))

            rows = cursor.fetchall()
            str_rows = []
            for row in rows:
                c = row[0]
                t = row[1]

                clean_text = script.cleanText(t, stopword = args.stopwords)
                clean_row = f"{NAMEDICT[c]}: {clean_text}" if c in NAMEDICT else 'None'
                str_rows.append(clean_row)

            allText += "\n"
            allText += "\n".join(str_rows)

    print()

    messages = [
            {'role':'user', 'content':'Context:'},
            {'role':'user', 'content':allText},
            {'role':'user', 'content':'User Query:'}
        ]
    
    chat = Chatter(args.model)
    chat.chat(prompt, True, messages)

def display_percentage_range(upper_bound, lower_bound):
    if upper_bound < lower_bound:
        upper_bound, lower_bound = lower_bound, upper_bound
    
    width = 40  # Width of the display
    range_size = upper_bound - lower_bound
    
    if range_size > 100:
        print("Error: Range size exceeds 100%")
        return
    
    upper_limit = int(width * (upper_bound / 100))
    lower_limit = int(width * (lower_bound / 100))

    print(f"ll: {lower_limit}")
    print(f"ul: {upper_limit}")
    print(f"W: {width}")
    
    display = [' '] * width
    for i in range(lower_limit, max( len(display)-1, upper_limit + 1)):
        display[i] = '#'
    
    print(f"{lower_bound}% {''.join(display)} {upper_bound}%")
    

if (__name__ == "__main__"):
    main()

