

import argparse
import os
import openai

from scripter import Scripter 
from scripter import NAMEDICT
from tokenizer import Tokenizer
from timeline import Timeline 

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_AUTH")

SETUP = """
This is a transcript from a dungeons and dragons game.
For each line of the transcript, you will see the following information: 

<class>: text

The class represents a player and the text represents something said by that player.
For context, below are all available classes and their associated DND role / character:
    <1> : DM
    <2> : Likkvorn
    <3> : Russet Crow
    <4> : Lief Bottom
    <5> : Oskar Rumnaheim
    <6> : Isra Lightfyrn

Here is all the world lore: 
Lore of the world: 
	Magic doesn’t just exist. It is pulled from somewhere, like water pulled from a well.  Those capable of turning the crank can dip their bucket into the reserve, wrenching from it great potential. Except, the bucket is not always ready to be dipped into the reservoir. The rope it dangles from stretches and springs with time, only long enough to touch the well’s bottom on special occasions. 

	1000 years have passed since anyone was last able to dip into the well of magic. In that ancient age, wizards and fae danced with liches and ghouls like the leaves dance on the breeze of an autumn day. To see a spell cast or ritual made was commonplace. But those days are gone. 

The great conflicts that come with magic’s power are discussed only in books and bard songs. Those artifacts which once brought fortune to those who wielded them sit inert on display. Those dynasties forged with mystical flame sit unmolested as unwavering pillars of power. 

This is not, however, a story of days gone by. This story is yet to be written, because magic’s waters are newly rippling with man’s touch, and the realm will never be the same again. 


Where does this take place?
World: Eversland 
Location: Province of Stonegate 
This area is lorded over by the Dwarves of Stonegate, a city near the coast built into a mountain range. This city serves as the port for the province where its positioning situates it as a strategic strong point. 
The Dwarves have ruled for 1000 years, making use of their long lifespan and strategic placement to hold onto the power granted to them by the conflicts settled 1000 years ago. 
NOTE: Should figure out what those conflicts were, as they will likely affect parts 3 and 4.
Features: 
The province is bordered on the north and west side by the Glittering Hills, a mountain range notable for the way the minerals in the rock glitter in the sunlight.
The province is bordered on the east and south side by The Gemtide Sea.
River: Moradin’s Sprue. 
Moradin is the main god in the dwarven pantheon
Sprue is the channel molten metal flows down on the way to the mold 
The river begins in the Glittering Hills and ends in The Gemtide Sea.
5 Cities sit along Moradin’s Sprue:
All 5 cities sit on the south-side of Moradin’s Sprue
Timberhold
The source of lumber in the Stonegate  
Sits at the base of the Glittering Hills 
The Forest: The Emeraldleaf Woods
The smallest of the cities
Rockwell
The mining and forgery hub of Stonegate 
The second most populous city of the Province 
Sits deep in the Glittering Hills 
Source of significant wealth in the region in the form of precious metals and gems 
Berronar’s Bossom (rough translation from dwarvish)
The farming and agricultural hub of the province
Responsible for feeding the surrounding cities
Due to food accessibility, this has also become a notable area for artisan trade 
Marthammor (named after the dwarven god of wanderers) 
Second largest city in the province
Hub of culture and learning, due to the pull of those with no other place to go
Stonegate: 
Heavily fortified seat of power for the province 
Seat of the throne, built deep into the sea-side cliffs of Stonegate
A massively constructed stone-wall (stone gate) surrounds and fortifies the city on all sides, both land and sea 
The Swallowed Swamp: 
The bog sits on the north side of Moradin’s Sprue.
When this region has essentially devoid of established power, a powerful lich, Lord Nethergloom, summoned a dark swamp into existence which threatened to consume the young province 
With the help of an infant Stonegate, and the Sorcerer Lirien Meadowkin, a party was able to penetrate The Swallowed Swamp and fell Lord Nethergloom.

Themes: 
The struggle for power
The road to hell is paved with good intentions 


Overall plot: 
	This campaign is about the struggle for power, and what that struggle leads people to do. This struggle for power will take place over 4 scales: 
Personal power         (1-5)
Institutional power     (6-10)
Authoritarian power   (11-15)
Cosmic power           (16-20)
	The source of this power lies in the plane of magic. With the rippling upon us, many are tuned into the fact that times are changing, and some are prepared to seize this day. As the players grow more powerful, they will learn the depths this struggle for power reaches, and engage with the different levels. The four scales above represent four sections of the progression from level 1 to 20.




Personal Power: 
	A fledgling necromancer, Finley Tuneweaver, was among the first normal people to hear the call of magic. Studying the ways of the millennium at the university of Marthammor, he was in a prime spot to tune into the realm of magic when it began to draw near to the realm. His studies revealed the potential magic held, and an idea began to form in Finley’s head.

	As the rippling begins, Finley can leverage the power granted to him to bring perfect peace to Stonegate and, possibly, the world. Finley had read about The Swallowed Swamp and had an idea. Legend of the Swamp said that some piece of Lord Nethergloom still sat there. He traveled to the swamp’s heart and, to his amazement, found just what he was looking for: Lord Nethergloom’s nearly depleted phylactery. 

	With a magical battery in his hands, Finley started to hatch a plan. If he could channel the remaining power into an army of golems, they could act as the region’s peace-keeping force, avoiding any need for loss of mortal life. Little did he know that, while Finley was working on his plan, another creature was working on a plan all their own. Sensing his phylactery disturbed, the remnants of Lord Nethergloom began to wake. 

	Finley’s initial experiments were unsuccessful. The phylactery was simply too depleted to make anything work. It was when he was most hopeless that Nethergloom set his own plan into motion. He began whispering to Finley ideas, incepting them where once there was nothing. Finley believed these thoughts to be his own, and set about charging the phylactery himself. 

	The efforts started simply with Finley capturing swamp creatures and feeding their immortal souls to the magical battery. Finley was unwittingly charging up the lich’s power, thinking he was charging his own. 

	As the phylactery grew fuller, so did the lich’s power. This was exerted in an equal growth of strength of the Swallowed Swamp. Those magical enchantments which had been dormant for 100’s of years slowly began to take hold of the land. The Swallowed Swamp began to eat once more. 

	All this while Finley is growing more knowledgeable as a wizard, reading the books he brought along with him and using his abilities to further his efforts. However, the souls of swamp critters are not sufficient to power a peace keeping force. So, believing himself to be acting righteously, Finley began to gather more souls. He started with those humanoid creatures who had made the swamp their home in the centuries following Nethergloom’s defeat. At this point Finley starts to gain traction. He is able to charge small golem creatures, born of flesh and imbued with his will. Where Finley’s corrupted vision saw beauty, the truth showed horror. He was using the spent physical forms of those whose souls he stole to create homunculus creatures he would use to do his bidding, and all the while Nethergloom was growing more powerful. 

	But once again, Finley’s aspirations grew larger than his abilities. He needed more. The souls he wrought from the swamp were already too corrupted to be used to bring about peace. In his eyes, the only souls who would suffice could be those of children. So began his master plan. With the help of his crude homunculus creatures, Finley began to reach out for help. He built a small cabal of co-conspirators, who would help him gather those who needed to be got.


SO, THIS ^^ DESCRIBES THE OVERALL SETUP FOR LEVELS 1-5. I PLAN TO HAVE 6-10 BUILD UPON THIS, BUT THAT WILL COME LATER. LEVELS 1-5 WILL REVOLVE AROUND LEARNING ABOUT FINLEY’S DOINGS, GATHERING MATERIALS TO PENETRATE THE SWALLOWED SWAMP, AND STOP FINLEY AND, ULTIMATELY, THE LICH. 

Institutional Power: 
	Stonegate and the surrounding region were nearly decimated during the last rippling. In that time, Lord Nethergloom’s forces had nearly overrun the region, taking all culture, industry and development along with. However, The Wisps were able to galvanize Stonegate’s armies, forcing back Nethergloom and eventually winning the day. This victory was, however, bittersweet for Stonegate. It became a stark reminder of just how fragile all this can be, and so they set about making preparations. 

	The seat of power in Stonegate belongs to the dwarven family known as The Ironshale. First of his name, Hardnose Ironshale, helped to found Stonegate during the first rippling and served as Lord Chieftain until his death 200 years later. 

	The start was simple. The city was built into the hill and surrounded by hulking, nearly impenetrable stone walls. This was well within the dwarven wheelhouse, and they ornamented their battlements with all manner of dwarven ingenuity. The next step, however, required some doing. It was always known that the rippling would return, it was just unclear 



How is Finley affecting the world right now?
Finley began his efforts 5 years ago, as the rippling was just starting. His mind has been very slowly corrupted over this time
He has expended the souls in most of the very sparse-ly populated villages in the swallowed swamp
Finley and his forces have only just arrived in Timberhold, Berronar’s Bossom, and Rockwell.
The swamp has only just started creeping over the bridge 
The kids have only just started going missing 
Finley must run most of his own errands, as his experiments aren’t currently turning out and he is still the Nethergloom’s puppet. 
Finley has created an outpost 1 day’s walk from Timberhold and set up the following things: 
1) An unseen servant, manifest from an amulet 
2) A haunted painting of a ghost, put under Nethergloom’s thrall. 
The amulet is taped to the back of the painting. The ghost in the painting can use the amulet to walk around
This will also be a gift to the players 
The ghost painting prepares the children to go into the forest, where they meet Finley
Finley has taken 3 children from Timberhold, which has certainly peaked the interest of the town’s people. 
The parents of many children are conspiring at night to do something, behind the backs of the authorities who claim to have things covered and want to keep the peace. 


Lord Nethergloom: 
	LNG started life as Herbert Willowspring, a scrappy elf living in a tiny village not far from where Timberhold is now. Herbert worked as a mail man, but it was only to pay for his passion of gardening. Living amongst the trees, he could cultivate such wondrous tiny worlds, home to fungus, sprouts, and even bugs. They were his to touch and prod at will, and he loved them.
	Delivering mail one day, Herbert felt a pull from his satchel. He went home from work with one too few packages delivered, and unwrapped what he had stolen to find a book full of characters he didn’t understand. The longer he spent with them, the more they twisted themselves into shapes he recognized and Herbert couldn’t believe what he saw. 
	The book spoke of powers beyond his imagination, capable of making possible his wildest dreams. Herbert had only one dream. He wished to make the whole world his garden, so that he could do with it what he pleased. And so, tome in hand, Herbert set off to the old woods, to study.
	Making the phylactery was the easy part. The soul of his brother did fine to get the thing started. The hard part was growing the swamp. Using the powers granted by the book and the souls stashed away in his phylactery, Herbert molded the land north of Moradin’s Sprue, forming The Swallowed Swamp.
	
Liren Meadowkin: 
	Liren, a Forest Dwarf from Timberhold, is born 100 years after Lord Nethergloom finds his Tome as the ripple comes into full swing. Riding a crest of the Ripple, Liren finds he has powers at an early age when he accidentally kills his brother in a hunting accident. Looking out over a cliff, seeing the beauty of the place he called home, Liren was overcome with a swell of energy, which manifested as a thick sheet of grease on the forest floor. His brother, who had just arrived at Liren’s request to see the view, slipped, tumbling off the ledge they stood.
	Liren, now seemingly cursed with these abilities, set out to find a way to control his powers, so that no one was ever hurt in the way he hurt his brother. While on his journey, Liren made friends with a gang of adventurers, who called themselves The Wisps. Together, they fought and destroyed Lord Nethergloom as level 10 adventurers. They went on to do many other great things, which I will figure out later. 
	Upon defeating Nethergloom, Liren returned to his hometown, Timberhold, to erect a crystal. This crystal, known as The Szafirleśny (Wooded Sapphire in Polish) protects Timberhold, acting as a barrier against the ever encroaching Swallowed Swamp.
The Wisps: 
Liren Meadowkin (M | Forest Dwarf)     - The Crystalline Wizard (Sorcerer) 
Alder Swiftblade (F | Human)                - The Blade of Berronar   (Rogue) 
Eleri Dawnstrike (M | Mountain Dwarf)  - Dreamblade         (Barbarian) - Married to Kaelen
Kaelen Mistwalker (F | Elf)                    - Stormfox                      (Druid) - Betrayed Party
	The Wisps were the legendary adventuring party of old. The realm knows them as their savior during The Rippled War. What they don’t know is that Kaelen was partially responsible for the war in the first place, after being manipulated by some force that sought out the power of the ripple. 
	Liren’s story is affecting part 1. I would like Alder’s story to affect part 2. I already have some ideas there. Notably, Alder was a sneaky rogue who may have had to sneak into Stonegate back in the day when it was just starting out. Maybe the party could uncover something he put in place to make it easier to sneak back in. Maybe they could discover an artifact he used to sneak around. I am not sure, but there is a lot there.
	When the party is learning about Kaelen, they will slowly realize that she was partially responsible for the Rippled War. Maybe that same force will reach out to one of the party members. Maybe the players will learn something about Eleri, Kaelen’s wife, which will make them realize something horrible happened? Who knows.
	I think Eleri will probably die in the rippled war. Maybe this is the event that turns Kaelen back to the light and allows her to help fight back the great evil. 

What does Finley have the children write? 
	“Mom and Dad. Please don’t be mad, but I have to go. I promise I will be back. Please don’t worry. I love you both!”


Why isn’t Timberhold getting help? 
Stonegate is aware of Finley’s doings in The Swallowed Swamp and is using him in an attempt to build a peacekeeping force 
Har Barkem started out messaging Stonegate, and originally received no reply
However, after the third letter, Har received a mysterious message which only asked Har to have patience. THe letter communicated that Stonegate was dealing with their own problems and would send help as soon as there was help to send. The message was accompanied by an automata (<4>’s character). 
Since then, Har has received a steady stream of slightly magical trinkets for his silence in these matters. 
He has also maintained a guise of Stonegate sending help as soon as possible, attempting to keep the peace. 

Message in the Wooded Crystal: 
Years ago, Liren suspected that The Wisp’s efforts may not be sufficient to stop Nethergloom’s darkness from resurfacing. 
To this end, Liren created a map to the various Swamp-navigating artifacts he believes should help any new adventurers work their way through the dangerous swamp. 
The artifacts are: 
1) Moradin’s Forge Lamp (Berronar’s Bossom)
2) Nethergloom’s Finger (Rockwell)
3) Port of Wisps (Stonegate - See Weiry (DM NOTE: animated book lost in the collapsed archives))
Liren has included the following message with the map: 


To whom it may concern,

You are now in possession of a quite important map created by a long-gone and severely missed Liren Meadowkin. 

If you are reading this note then the Szafirleśny must have been damaged, and if the Szafirleśny has been damaged that can mean only one thing: nards.

We missed something and now Nethergloom has probably returned. Sorry… 

We all agree it’s a bad deal, so IF it happens, we wanted to have a contingency. 

This map holds the locations of 3 2 things we find to be quite useful. If ‘ole Gloomy is pulling up his waders, he’ll be doing it somewhere in that swamp of his. Make use of these gifts and finish what we started, please. 

My deepest <fill in later>. 

Stuff: 
Moradin’s Forge Lamp (found in Temple of Moradin, Berronar’s Bossom)
Port of Wisps (Stonegate, talk with Weiry)

Best of luck! If you mess up, we’ll chat about it on astral time. 

P.S. Kaelen ruined my art and ripped the map, so I guess were going to let #2 stay gone... She says it’s “too dangerous”. Doesn’t even care I made that riddle… 

The tree also contained: 
1x original Stonegate gold coin, with a W carved in the ‘Tails’ side 
This was an original belonging of the Wisps and one of the first gold the party received on their journey.
This coin would mean a lot when shown to the correct people. 


***
END OF LORE 

please use that as context when creating your bulleted list of campaign events from the transcript you read. 
Be sure to record anything related to the world lore, and be free to infer from what is discussed. 
also you should know that stopwords have been removed. 
""" 


"""
This is a transcript from a dungeons and dragons game.
For each line of the transcript, you will see the following information: 

<class>: text

The class represents a player and the text represents something said by that player.
For context, below are all available classes and their associated DND role / character:
    <1> : DM
    <2> : Likkvorn
    <3> : Russet Crow
    <4> : Lief Bottom
    <5> : Oskar Rumnaheim
    <6> : Isra Lightfyrn

You are an intermediary. Your job is to take the chunks of transcript given
and summarize all events related to dungeons and dragons. You should write your 
recollection in paragraph form. Be detailed and thorough. Be sure to specify whether a player is doing something
or if that player's character is doing something.
""" 


"""
This is a transcript from a dungeons and dragons game.
For each line of the transcript, you will see the following information: 

<class>: text

The class represents a player and the text represents something said by that player.
For context, below are all available classes and their associated DND role / character:
    <1> : DM
    <2> : Likkvorn
    <3> : Russet Crow
    <4> : Lief Bottom
    <5> : Oskar Rumnaheim
    <6> : Isra Lightfyrn

The task is to create a bulleted list of campaign events and details.

YOU MUST mention specific details like spells cast and items interacted with. 
YOU MUST mention the specific character who did each thing. 
YOU MUST NOT make up any information.
YOU MAY disregard lines which seem unrelated to the campaign.

THINGS WHICH RELATE TO CAMPAIGN:
- game world, 
- characters, 
- actions, 
- spells, 
- npcs, 
- items, 
- interactions
- relationships 

"""



"""
This a transcript from a dungeons and dragons game.
For each line of the transcript, you will see the following information: 

<class>: text

The class represents a player and the text represents something said by that player.
For context, below are all available classes and their associated DND role / character:
    <1> : DM
    <2> : Likkvorn (Wizard, Necromancer, Gnome)
    <3> : Russet Crow (Sorcerer, Wild Magic, Kenku)
    <4> : Lief Bottom (Rogue, na, Elf)
    <5> : Oskar Rumnaheim (Artificer, Armorer, Dwarf)
    <6> : Isra Lightfyrn (Druid, Path of Stars, Dwarf)

The task is to create a list of tags which describe sections of the transcript. 


"""



"""
This a transcript from a dungeons and dragons game.
For each line of the transcript, you will see the following information: 

<class>: text

The class represents a player and the text represents something said by that player.
For context, below are all available classes and their associated DND role / character:
    <1> : DM
    <2> : Likkvorn (Wizard, Necromancer, Gnome)
    <3> : Russet Crow (Sorcerer, Wild Magic, Kenku)
    <4> : Lief Bottom (Rogue, na, Elf)
    <5> : Oskar Rumnaheim (Artificer, Armorer, Dwarf)
    <6> : Isra Lightfyrn (Druid, Path of Stars, Dwarf)
The task is to create a bulleted list of campaign events and details.
You should prepare this as if another dm was coming along and wanted to read about the campaign.

YOU MUST mention the specific person or character who did each thing. 
YOU MUST NOT make up any information.

Make the entries of high quality and representative of the campaign.
These should relate to the game world, characters, actions, spells, npcs, items, interactions, and relationships. 
Mention specific details like items interacted with, npc's spoken to, and 
"""

"""
For each line, please include a sentiment score describing your certainty what you have written relates to dungeons and dragons.
Your sentiment scores may be: low, medium, high.
"""

def make_parser():
    parser = argparse.ArgumentParser(description='Summarize and Timeline events from DND Transcript in MySQL DB.')

    parser.add_argument('-pr', '--prompt', type=str, help='Prompt to provide context for the summary generation', default=None)
    parser.add_argument("-s", '--session', type=str, help='Session Code', default=None, required=False)
    parser.add_argument('-sn', '--session_name', type=str, help='Session Name', default=None)
    parser.add_argument('-w', '--whisper', help='Name of the whisper model used to transcribe (for session id)', default='base.en', type=str)
    parser.add_argument('-m', '--model', type=str, help='GPT Model to use [gpt-3.5-turbo, gpt-4, gpt-3.5-turbo-16k]', default='gpt-3.5-turbo-16k')
    parser.add_argument('-m1', '--model1', type=str, help='GPT Model to use for second summary', default='gpt-3.5-turbo-16k')
    parser.add_argument('-ho', '--host', help='Database host', default='localhost')
    parser.add_argument('-u', '--user', help='Database user', default='ygg')
    parser.add_argument('-p', '--password', help='Database password', default='')
    parser.add_argument('-t', '--table', help='Database table', default='transcript')
    parser.add_argument('-db', '--database', help='Database name', default='yggdrasil')
    parser.add_argument('--halt', action="store_true", help='Will pause before sending each prompt')
    parser.add_argument('-tmln', '--timeline', action='store_true', help='Turn on to create Knowledge Graph timeline using gpt3.5-turbo-16k')
    parser.add_argument('-temp', '--temperature', type=float, help='chat gpt temperature', default=0)
    parser.add_argument('--clean', help='Clean text to anonymized and stripped', action='store_true')
    parser.add_argument("--stopword", help='Remove stopwords', action='store_true')
    parser.add_argument('--tokenlim', help='Limit for each batch, in tokens.', default=2000, type=int)
    parser.add_argument('--savepath', help='Location to save complete summary', required=True)

    return(parser)

def generate_summary2(prompt, script, df, model, halt, timeline, temp, tokenlim):
    summary = ""

    for ctr, chunk in enumerate(script.getAllTokenChunkBounds(df, tokenlim)[5:]):
        messages = []
        #messages.append({'role':'system', 'content':prompt})
        messages.append({'role':'system', 'content':prompt})

        messages.append({'role':'user', 'content':'Below is the transcript:'})
        messages.append({'role':'user', 'content':"\n".join(script.getClassTextStrRows(df, *chunk))})

        
        print("------------------ CONTEXT ------------------")
        for message in messages:
            print("{}\n{}".format(message['role'], message['content']))
            print("------------------------")


        if(halt):
            print()
            input('Send Prompt?')

        completion = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=temp
        )

        reply = completion.choices[-1].message.content
        summary += reply

        print("\n")
        print("----------- Reply -----------:\n{}".format(reply))
        if(halt):
            input()
        print("\n\n\n")

    #print(summary)
        
    return summary



def generate_timeline(path, prompt, batch_size, model, sl, halt, timeline, temp):
    script = Scripter()
    script.loadCSV(path)
    script.textPipeline()
    script.filterTranscript()

    tokenizer = Tokenizer(name=model)
    cum_cost = 0 

    if(timeline):
        session_timeline = Timeline()

    if('cost.txt' in os.listdir('./')):
        costs = open('cost.txt', 'a')

    summary = ""
    for i in range(0 + sl, len(script.df), batch_size):
        batch_message = script.combineRowList(script.getRows(i, batch_size), NAMEDICT)

        messages = []
        messages.append({'role':'user', 'content':"""#This a transcript from a dungeons and dragons game.
                        For each line of the transcript, you will see the following information: 
                        <class>: text
                        For context, below are all available classes and their associated DND role:
                         <1> : DM
                         <2> : Likkvorn
                         <3> : Russet Crow
                         <4> : Lief Bottom
                         <5> : Oskar Rumnaheim
                         <6> : Isra Lightfyrn
                        The task is to extract as many relevant entities to dnd, the game world, character actions, npcs, and spells.
                        The entities should include all locations, items, characters, and spells.
                        Also, return the type of an entity using the Wikipedia class system and the sentiment of the mentioned entity,
                        where the sentiment value ranges from -1 to 1, and -1 being very negative, 1 being very positive
                        Additionally, extract all relevant relationships between identified entities.
                        The relationships should follow the Wikipedia schema type.
                        The output of a relationship should be in a form of a triple Head, Relationship, Tail, for example
                        Peter, WORKS_AT, Hospital (any relevent metadata)/n
                         An example "St. Peter is located in Paris" should have an output with the following format
                        entity
                        St. Peter, person, 0.0
                        Paris, location, 0.0

                        relationships
                        St.Peter, LOCATED_IN, Paris\n"""}
                        )
        messages.append({"role":"user", "content":batch_message})

        print("------------------ CONTEXT ------------------")
        for message in messages:
            print("{}\n{}".format(message['role'], message['content']))
            print("------------------------")

        cstr = '\n'.join([message['content'] for message in messages])
        print("# Tokens: {:.2f} | ${:.4f} | ${:.4f} Total".format(tokenizer.calculate_tokens(cstr), price := tokenizer.calculate_price(cstr), price+cum_cost))
        cum_cost += price

        if(halt):
            print()
            input('Send Prompt?')

        costs.write('${:.4f}\n'.format(price))

        completion = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=temp
        )

        # Get the generated reply from ChatGPT
        reply = completion.choices[-1].message.content
        summary += reply

        print("\n")
        print("----------- Reply -----------:\n{}".format(reply))
        if(halt):
            input()
        print("\n\n\n")

        if(timeline):
            if(reply in ['No', 'no', 'n']):
                continue

            kd_reply = openai.ChatCompletion.create(
                model='gpt-3.5-turbo-16k',
                messages = [
                    {'role':'system', 'content':"Today we are going to build a knowledge graph. Here is some information about knowledge graphs: Knowledge graphs are structured representations of knowledge that organize information in a graph-like structure. They capture entities, their attributes, and relationships, enabling efficient data management and knowledge discovery. Here is how one should insert information into a knowledge graph: <subject> <predicate> <object><metadata>I am going to provide a rough summary of a DND campaign. I need you to think step by step, and go line by line, and break up each entry into a suitable knowledge graph entry. Please make each predicate as simple as possible. Output your response as numbered lines."},
                    {'role':'user', 'content':reply}
                ]
            )

        
    return summary


def save_summary(summary, save_path):
    with open(save_path, 'w') as file:
        file.write(summary)
    print("Summary saved successfully.")

def summarizeSummary(model, path):
    f = open(path, 'r')

    lines = f.readlines()

    
    setup = """
You will see a summary of a transcript of people playing dungeons and dragons.
your job is to take the information you see and use it to write an introduction
to a session of dungeons and dragons.
"""
    
    """
This is a rough bulleted list of events in a dungeons and dragons campaign. 
Your job is to chronicle the list's events in an informative way.
You want this to be clear and informationally dense.
Include information on the game world, characters, actions, spells, npcs, items, interactions, relationships, and more. 
"""

    if(model == 'gpt-4'):
        i = 0
        reply = ''
        while i < len(lines):
            c_lines = lines[i:min(len(lines)-1, i+5)]

            messages = [{'role':'user', 'content':setup}]
            c_lines = "\n".join(c_lines)
            messages.append({'role':'user', 'content':c_lines})

            print(messages)
            input()

            completion = openai.ChatCompletion.create(
                model=model,
                messages=messages
            )

            c_reply = completion.choices[-1].message.content
            reply += '\n' + c_reply

            i += 5

    else:
        messages = [{'role':'user', 'content':setup}]

        lines = "\n".join(lines)
        messages.append({'role':'user', 'content':lines})

        completion = openai.ChatCompletion.create(
                model=model,
                messages=messages
            )

        # Get the generated reply from ChatGPT
        reply = completion.choices[-1].message.content
    
    print(reply)

    return(reply)



if __name__ == '__main__':
    parser = make_parser()
    args = parser.parse_args()

    prompt = args.prompt
    if(not prompt):
        setup = SETUP
        prompt = setup
 
    script = Scripter()
    script.connectMySQL(args.host, args.database, args.user, args.password)
    df = script.loadMySQL(args.table, {'session':args.session, 'session_name':args.session_name, 'whisper':args.whisper})

    df.session_id = df.session_id.astype(int)
    #df = df[df.session_id > 3000]

    if(args.clean):
        df = script.cleanDFPipe(df, stopword=args.stopword)

    summary = generate_summary2(prompt, script, df, args.model, args.halt, args.timeline, args.temperature, args.tokenlim)
    save_summary(summary, args.savepath)

    model1 = args.model1
    if(not model1):
        model1 = args.model

    sumsummary = summarizeSummary(model1, args.savepath)
    save_summary(sumsummary, args.savepath.split(".")[-2] + '_summary.txt')