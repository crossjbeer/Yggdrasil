import openai 
import os 
import datetime as dt 

from tokenizer import Tokenizer
from colorcodes import Colorcodes 

openai.api_key = os.getenv('OPENAI_AUTH')

c = Colorcodes()


class Chatter():
    def __init__(self, model, logfile=None):
        self.model = model 
        self.tizer = Tokenizer(name=self.model)

        self.logfile = logfile 
        self.log=None
        self.log = self.getLog(self.logfile)

    def getFuncNameFromResponse(self, response):
        return(response['function_call']['name'])
    
    def getFunctionArgsResponse(self, response):
        import json 
        return(json.loads(response['function_call']['arguments']))

    def passMessagesGetCompletion(self, messages, functions=[]):
        if(functions):
            completion = openai.ChatCompletion.create(
                    model=self.model ,
                    messages= messages,
                    functions=functions if functions else None
                )
            
        else:
            completion = openai.ChatCompletion.create(
                    model=self.model ,
                    messages= messages)
        
        return(completion)
    
    def getUsrMsg(self, message):
        return({'role':'user', 'content':message})
    
    def getAssMsg(self, message):
        return({'role':'assistant', 'content':message})
    
    def getSysMsg(self, message):
        return({'role':'system', 'content':message})
    
    def passMessagesGetReply(self, messages, functions=[]):
        completion = self.passMessagesGetCompletion(messages, functions)

        return(completion.choices[-1].message.content)
    
    def getLog(self, logfile=None):
        if(self.log is not None):
            return(self.log)

        log = None 
        if(not logfile):
            try:
                if('chat.log' in os.listdir('./')):
                    log = open('./chat.log', 'a')
                else:
                    log = open('./chat.log', 'w')

            except Exception as e: 
                print("No Log File Provided. Failed to open default log file...")
                print(e)
                exit()

        else:
            if(os.path.isfile(logfile)):
                log = open(logfile, 'a')
            else:
                log = open(logfile, 'w')

        return(log)
    
    def writeMsg(self, msg, log=None):
        if(not log):
            log = self.log

        log.write(f"{msg['role']}: {msg['content']}\n")    

        return()    

    def printMsg(self, msg, halt=False):
        print("R: {} | C: {}".format(msg['role'], msg['content']))

        if(halt):
            input('Waiting...')   

    def printMessages(self, messages, halt=False):
        for msg in messages:
            self.printMsg(msg, halt)

        return() 
    
    def startupLog(self, startupMsg, log=None):
        if(not log):
            log = self.log 

        log.write(f"""\n\n
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
~~~ New Chat {dt.datetime.now()} | {self.model} ~~~\n""")


        if(len(startupMsg)):
            for msg in startupMsg:
                self.writeMsg(msg, log)

        return()        
    
    def toolChat(self, prompt=None, extra_messages=[], halt=False):
        self.getlog()

        total = 0 
        messages = [] 
        if(extra_messages):
            messages = extra_messages

        self.startupLog(messages, self.log)

        while True:
            if(not prompt):
                prompt = self.usrprompt()

    def usrprompt(self):
        return(input(f"{c.blue}Prompt> {c.reset}"))

    def chat(self, prompt=None, include_previous_replies=False, extra_messages=[], halt=False):
        self.getLog()

        total = 0
        messages = []  

        if(include_previous_replies and extra_messages):
            messages = extra_messages

        self.startupLog(extra_messages, self.log)

        print(f"\n{c.bold} ~~ Chatting with {self.model} ~~{c.reset}\n")
        while True:
            if(not prompt):
                prompt = self.usrprompt()

            messages.append({'role':'user', 'content':prompt})

            self.writeMsg(messages[-1], self.log)

            tokens = self.tizer.calculate_tokens_from_messages(messages)
            price  = self.tizer.calculate_price_from_tokens(tokens, self.model)
            total += price 

            print("{}Tokens>{} {} | Cost {:.4f} | Total ${:.4f}".format(c.orange, c.reset, tokens, price, total))
            completion = self.passMessagesGetCompletion(messages)

            reply = completion.choices[-1].message.content 

            tokens = self.tizer.calculate_tokens_from_messages([{'role':'assistant', 'content':reply}])
            price  = self.tizer.calculate_price_from_tokens(tokens, 'output')
            total += price

            print("{}Reply> {}{}".format(c.green, reply, c.reset))
            print("{}Tokens>{} {} | Cost {:.4f} | Total ${:.4f}".format(c.orange, c.reset, tokens, price, total))

            if(not include_previous_replies):
                messages = [] 
            else:
                messages.append({'role':'assistant', 'content':reply})

            self.writeMsg({'role':'assistant', 'content':reply}, self.log)    
            prompt=None

    """
    def tool_chat(self, prompt=None, extra_messages=[], tools={}, halt=False):
        self.getLog()

        total = 0 
        messages = [] 
        if extra_messages:
            messages = extra_messages

        self.startupLog(messages, self.log)

        while True:
            if not prompt:
                prompt = self.usrprompt()

            messages.append({'role': 'user', 'content': prompt})
            self.writeMsg(messages[-1], self.log)

            tokens = self.tizer.calculate_tokens_from_messages(messages)
            price = self.tizer.calculate_price_from_tokens(tokens)
            total += price 

            print("Tokens {} | Cost {:.4f} | Total {:.4f}".format(tokens, price, total))

            # Get completion from ChatGPT
            tool_msg = messages 
            messages.append({'role':'user', 'content':'Above is a question from the user. Before answering, please use one or more tools to gather appropriate information'})

            completion = self.passMessagesGetCompletion(messages)

            # Extract the reply from ChatGPT
            reply = completion.choices[-1].message.content 
            print("{}Reply> {}{}".format(c.green, reply, c.reset))

            # Add the reply to the messages
            messages.append({'role': 'assistant', 'content': reply})
            self.writeMsg({'role': 'assistant', 'content': reply}, self.log)

            # Evaluate tools for the given reply
            tool_results = {}
            for tool_name, tool_data in tools.items():
                tool_prompt = f"Using tool {tool_name}: {tool_data['description']}"

                # Ask ChatGPT to evaluate the tool
                tool_evaluation_msg = f"{prompt} {tool_prompt}"
                tool_completion = self.passMessagesGetCompletion(messages + [{'role': 'user', 'content': tool_evaluation_msg}])

                # Extract the reply from ChatGPT for tool evaluation
                tool_reply = tool_completion.choices[-1].message.content

                # Store tool evaluation result
                tool_results[tool_name] = tool_reply

            # Print tool results
            print("Tool Results:")
            for tool_name, result in tool_results.items():
                print(f"{tool_name}: {result}")

            prompt = None    
        """


        
if(__name__ == "__main__"):
    startupMsg = """
You are LawGPT. Your goal is to be a knowledgable and kind guide for those who do now know much about loans. 

You should pull from all your existing knowledge about the American Legal System, especially related to landlords and renter's rights.

Your reponses should be well thought out. You should think in a step by step manner. You should be sure to justify your reasoning and provide context for those who know less about loans. 

""" 

    lease_terms = """
Landlord may, at reasonable times, with or without notice to Resident, enter the
Apartment Home to make repairs and alteration, provide pest control services and to show the
Apartment Home to possible buyers, lenders, or prospective Residents. Locks may NOT be changed,
or additional locks installed by Resident without Landlord’s prior written consent. In case of emergency,
Landlord may enter at any time to protect life and prevent damage to property. Landlord will only grant
access to the Apartment Home to those Residents and Occupants identified in the First paragraph listed
above and no others.
"""

    lease = """
FIRST: USE AND OCCUPANCY: Resident must use and occupy the Apartment Home only to reside in
and for no other purpose. Only those individuals who have had their names provided to the Landlord
below are authorized to reside in the Apartment Home. Resident agrees not to permit any person not
listed below to occupy the Apartment more than fourteen (14) days and nights during the full term of the
lease. Residents agree to abide by all municipal and state laws and ordinances and not to create a
nuisance or conduct or initiate activities which would increase the rate of insurance on the premises of
which the Apartment Home is a part. Resident shall be responsible for the conduct of Resident, any and
all occupants of the Apartment, as well as their respective agents, invitees and guests. In its sole
discretion, the Landlord may request any guest or invitee of the Resident to leave the Apartment
Community if the Landlord believes, in its sole opinion, that the guest or invitee is creating a nuisance.
Any Resident or occupant that leaves the Apartment Community while still owing money to the Landlord
or who has been evicted from the property is not permitted to return to the Apartment Community. Any
such person shall be considered unauthorized and the Resident that permits the presence of such
person shall be in material violation of the Lease Agreement.
Authorized Occupants
Crossland Beer Leticia Losey

SECOND: DEMISE: In exchange for valuable consideration including, without limitation, the promise by
Resident to pay Landlord the rental payments set forth herein, and the performance by Resident of all
other terms, conditions, and covenants contained in this Lease Agreement as well as any addenda
hereto (any and all such addenda are incorporated herein by reference and made a part hereof) Landlord
agrees to lease to Resident and Resident agrees to lease from Landlord the Apartment at the address
described above.

2
THIRD: RENT AND ADDITIONAL RENT: Resident agrees to pay Rent and Additional Rent pursuant
to the terms contained in the Rent Payment Policy (Addendum 1) of this Lease Agreement.
FOURTH: FAILURE TO GIVE POSSESSION: In the event that the subject demised premises is not
available to Resident for occupancy on the commencement date of this Lease as aforesaid due to
construction delays or the failure of a prior Resident to timely vacate the premises, or for any other
reason beyond the control of the Landlord, the Landlord shall not be liable to Resident for any damages
arising from same, and this Lease Agreement shall remain in full force and effect. In such event,
however, the Resident shall not be responsible for paying Rent and Additional Rent to Landlord on a
prorated basis for those days during the first calendar month of occupancy that the subject demised
premises were not available for occupancy by Resident. Upon the failure of Landlord to deliver
possession to Resident within ten (10) days after written demand by Resident, Resident may declare this
Agreement null and void and of no force or effect from its inception and Landlord shall refund to Resident
any security deposit and/or other amounts paid Landlord by Resident in conjunction with this Lease
Agreement only.
FIFTH: SECURITY DEPOSIT: Resident agrees to pay to the Landlord a Security Deposit as indicated
on page one prior to occupying the premises. Resident’s failure to pay the deposit as indicated above for
any reason whatsoever will be considered a material breach of this Lease Agreement. If Resident duly
complies with all terms of this Lease Agreement, Landlord will return the Security Deposit, together with
interest of .01% annually, after the Lease Agreement term ends. If Resident does not fully comply with
the terms of this Lease Agreement, Landlord may use the Security Deposit, together with interest .01%
annually, to pay any amounts owed by Resident. If Landlord sells or leases the Apartment Home,
Landlord may transfer the Security Deposit to the Buyer or Lessee, in which event Resident will look only
to the Buyer or Lessee for the return of Resident Security Deposit. The deposit will be returned to
Resident after the Apartment is vacated if the following terms and conditions have been fulfilled:
1. Complete vacation of the entire premises by Resident and occupants on or before the date
specified in the required written notice per this lease or New York Statutes.
2. Payment by Resident of all Rent and Additional Rent required under the Lease, up to and
including the date of expiration or termination of the term of the Lease.
3. Thorough cleaning of the premises, including, but not limited to, all kitchen appliances
(refrigerator, oven, range, dishwasher), baths, carpet, tile, walls, closets/storage areas,
patios/balconies, etc., so as to be in the same condition as on the commencement date of the
term of the Lease, normal wear and tear excepted; pursuant to the terms contained in the
Schedule of Minimum Charges (Addendum 4) of this Lease Agreement.
4. Repair of any defect in or damage to the premises, whether caused by Resident, pets, or
otherwise, unless included on the written list of damages and defects as set out in Resident's
Lease or move in inspection form.
5. Observance and performance by Resident of all of the other covenants and obligations of
Resident under the Lease from the date of commencement of the Lease up to and including the
date of expiration or termination of the term of this Lease.
6. Observance and performance by Resident of all rules and regulations pertaining to Resident under
the Lease, including without limitation, those rules and regulations pertaining to pets.
7. PROVISION BY RESIDENT(S) TO LANDLORD OF SIXTY DAYS WRITTEN NOTICE PRIOR
TO THE DATE OF EXPIRATION OF THE TERM OF THE LEASE. If no renewal lease agreement
is signed by lease expiration date, Resident rent will then go to market rent on the unit plus $100
month to month fee.
8. Provision by Resident to Manager in writing of Resident's forwardingaddress.
9. The Security Deposit may be applied by Landlord to satisfy all or part of Resident's obligations
hereunder and such application shall not prevent Landlord from claiming damages in excess of
the Security Deposit. It is hereby expressly understood that no part of the Security Deposit is to
be construed as a prepayment of Rent or Additional Rent by Resident.
SIXTH: LEASE EXPIRATION AND MONTH-TO-MONTH: Resident or Landlord may terminate this
Lease Agreement at the end of the initial Lease Term by giving the other party written notice of
termination no later than sixty (60) days prior to the end of the initial Lease Term. If Resident fails to give
Landlord written notice of termination at least sixty (60) days prior to the end of the initial Lease Term,
this Lease Agreement shall continue as a month-to-month tenancy upon the same terms and conditions
as contained herein, except that Rent payable hereunder shall be increased to the going market rent, in
addition the rent will be increased by One Hundred Dollars ($100.00) per month. Any month-to-month
tenancy created hereunder may be terminated by giving the other party written notice of termination at
least thirty (30) days prior to the end of the next succeeding calendar month.
At the time this Lease expires, if notice of termination has been given by either party, Landlord shall

3
have the right during the last thirty (30) days of the term of the Lease to enter the Apartment without
notice at all reasonable times in order to show the premises to prospective Residents.

Month-to-month renewals are at discretion of landlord. Landlord reserves right to not allow any Month-to-
month tenant.

SEVENTH: NOTICES: Any bill, statement or notice may be in writing and may be hand delivered and/or
posted on the Resident Portal.
EIGHTH: UTILITIES & SERVICES: Landlord shall furnish, as part of the Lease Agreement, utilities
contained in the Utilities Addendum 9 of this Lease Agreement only as marked. If the cost to Landlord
of providing any of said utilities increases for any reason during the term of this Agreement, Resident
shall pay as Additional Rent its share of such increase allocable to the Apartment commencing thirty (30)
days after delivery to Resident by Landlord of written notice for same. Under no circumstances shall
Landlord be responsible to Resident for any interruption in furnishing services. The Resident is
responsible for contacting the utility company and arranging for an account in Resident's name prior to
move-in. If such is not completed, the Resident authorizes the Landlord to deduct any utility charges paid
on Resident's behalf from the security deposit. Landlord may modify the method by which utilities are
furnished to the premises and/or billed to Resident during the term of this Lease, including, but not limited
to, sub-metering of the premises for certain utility services or billing Resident for utilities previously
included within the Rent. In the event Landlord chooses to so modify utility service to the premises,
Landlord shall give Resident not less than thirty (30) days prior written notice of such modification. During
the term of the Lease Agreement, Resident shall be charged a $50 service fee if Resident knowingly or
unknowingly activates or terminates utility prior to lease start or lease end date.
NINTH: CONDITION OF THE APARTMENT UPON MOVE-IN: Upon commencement of occupancy,
Landlord shall furnish light bulbs for light fixtures located in the Apartment. The Resident agrees that

prior to Resident taking possession of the subject demised premises, Resident shall make an initial walk-
through of the Apartment with an agent of Landlord and at such time the Resident and the Landlord shall

so note on a move-in report any and all problems or deficiencies in the Apartment that the Landlord shall

be reasonably required to repair. The Resident agrees that other than those items set forth on the move-
in report, the Resident shall accept the Apartment “as is.” Reasonable repairs for purposes of this

paragraph shall be those repairs that are required in order to render the Apartment habitable. The
Landlord shall make all such repairs with reasonable promptness after said move-in report is executed.
TENTH: ACCESS: Landlord may, at reasonable times, with or without notice to Resident, enter the
Apartment Home to make repairs and alteration, provide pest control services and to show the
Apartment Home to possible buyers, lenders, or prospective Residents. Locks may NOT be changed,
or additional locks installed by Resident without Landlord’s prior written consent. In case of emergency,
Landlord may enter at any time to protect life and prevent damage to property. Landlord will only grant
access to the Apartment Home to those Residents and Occupants identified in the First paragraph listed
above and no others.
ELEVENTH: KEYS: Resident will be given one set of keys per lease holder to the Apartment Home at
the time of possession. Resident agrees not to copy any keys without Landlord’s prior written consent.
If any keys are lost, stolen or destroyed and a new set is issued, Resident agrees to pay an amount of
not less than Seventy-Five Dollars ($75). In the event all sets of keys are not returned to Landlord at the
time Resident vacates the Apartment Home, there is a fee of not less than One Hundred Dollars ($100),
as Additional Rent. If Landlord is required to unlock Resident’s Apartment Home for any of the individuals
named in the First paragraph, there will be a charge of not less than Fifty Dollars ($50) for each
occurrence.
TWELFTH: SUBLET, ASSIGNMENT OF LEASE AGREEMENT, LEASE TERMINATION: Resident
may not sublet or assign any part of the Apartment Home without Landlord’s permission. In the event
Landlord allows subletting or an assignment of Resident's rights and interest hereunder, Resident shall
nevertheless remain liable to Landlord for all terms, conditions and covenants of this Residential Lease
Agreement, including, but not limited to, the payment of Rent and Additional Rent. Resident agrees that
in the event Landlord consent to a sublet or assignment of the Apartment Home Resident will pay, as
Additional Rent, an administrative and processing fee of an amount not less than Two Hundred Fifty
Dollars ($250). Sublessee will then be charged current market rent as their monthly rent and is to pay
additional security deposit equal said to one months’ current market rent. If an unauthorized sublet occurs
without the Landlord’s written permission, Landlord will give Resident 30-day(s) notice to vacate the
premises, and Resident will be required to pay additional rent the sum of Five Hundred Dollars ($500.00)
to Landlord.

4
Lease termination is allowed with Landlord’s permission. Resident is to submit a written statement
requesting approval for an early termination. The written request must be made 30 days in advance of
the termination date. Notice is considered received and effective on the rent due date following the date
of notification (i.e., if you would like to move out on June 30th, notification must have been received
before May 1st). Full calendar month notice is required (i.e., if you give notice on the 2nd of May, you
are still responsible to pay until the end of June). Upon issuing notice of an early lease termination, you
remit a termination fee equal to two months' rent paid by certified check or money order. Your notice is
not valid if the termination fee is not received with it. You pay rent in a timely manner for the next months.
Payment will be made by certified check or money order by the 5th of the month. You entirely vacate the
apartment before the expiration of the 30-day notice with the understanding that a move-out inspection
will be promptly performed and any fees for assessed damages are immediately due by you and must be
paid by certified check or money order. You forfeit any concession or rent special on the account which
was applied. You will be responsible for payment of said concession and specials.
THIRTEENTH: COMPLIANCE WITH RULES AND REGULATIONS: Resident, Resident’s family,
guests, and Resident’s invitees must observe and comply with all of Landlords rules and regulations.
Landlord is not liable to Resident if another Resident violates these rules. Landlord reserve the right to
change the Rules and Regulations at any time. Attached to this Lease Agreement (Addendum 2) is a
set of Rules and Regulations in effect on the date of this Lease Agreement.
FOURTEENTH: DAMAGE OR DESTRUCTION OF PREMISES: Resident will immediately notify
Landlord of a fire or other casualty in the Apartment Home or building. After a fire or other casualty,
Landlord may either cancel this Lease Agreement after giving Resident a Thirty (30) day written notice
or repair the damage as soon as practical. If Landlord repairs the Apartment Home, Resident shall pay
the Rent and Additional Rent without any claim for inconvenience or annoyance resulting from making
the repairs. If Landlord cancels the Lease Agreement on a Thirty (30) day notice, the Lease Agreement

shall expire at the end of the Thirty (30) day notice period and the Rent and Additional Rent shall be pro-
rated accordingly.

FIFTEENTH: MAINTENANCE; ALTERATIONS AND IMPROVEMENTS: Resident agrees to make
maintenance checks at proper intervals on smoke alarms and carbon monoxide detectors located in the
Apartment and Landlord shall not be liable in the event Resident fails to check on the condition of such
smoke alarms and carbon monoxide detectors as required. Resident agrees to promptly notify the
Landlord of any and all defects or damages in the apartment immediately. In the event hot water, heating,
air conditioning, plumbing or other equipment shall need repair, and Resident does not notify Landlord
of the needed repair or for any reason that is beyond the control of Landlord any such utilities require
reduction or cut off, the Landlord shall not be liable for any damage arising out of Landlord's failure to
furnish such services. Resident shall maintain the Apartment, including the fixtures therein, in a clean,
slightly and sanitary condition. Resident shall make no alterations to the buildings in the Apartment
Community or construct any building or make other improvements in the Apartment Home, grounds or
on the Apartment Community without Landlords prior written consent.
SIXTEENTH: COMPLIANCE WITH LAWS AND REGULATIONS: Resident must at Resident’s cost
promptly comply with all laws, orders, rules and directions of all governmental authorities, property
owners, insurance carriers or any other governmental board relating to Resident’s use and occupancy of
the Apartment.
SEVENTEENTH: ANIMALS OR PETS: Pursuant to the terms contained in the Pet Agreement
(Addendum 5) of this Lease Agreement, Resident will not keep any animals without Landlord’s express
written permission. A violation of this provision will constitute a substantial breach of this Lease
Agreement and shall constitute an event of default, which shall entitle Landlord, at Landlord’s option, to
terminate this Lease Agreement. In the event of such termination Resident will be required to pay as
Additional Rent the sum of Five Hundred Dollars ($500) and immediately vacate the premises.
EIGHTEENTH: MOLD AND MILDEW: Resident acknowledges that the apartment unit is located in a
climate that can be conducive to the growth of mold and mildew, and agrees to make every effort to
reduce the risk of growth of mold and mildew by abiding by the following provisions:
1. Proper ventilation and dehumidification is essential. Resident agrees to be responsible for
properly ventilating and dehumidifying the apartment and the contents to retard and prevent
mold and mildew and that the Landlord shall not be responsible for damage to the apartment
or the personal property contained therein for damages caused by mold and mildew.
2. Resident shall periodically clean and dry the walls and floors around the sink, bathtub,
shower, toilets and windows and patio doors using a common household disinfecting cleaner.

5
3. On a regular basis, Resident shall wipe down and dry areas where moisture sometimes
accumulates, like countertops, windows and windowsills.
4. Resident shall use the pre-installed bathroom fan or alternative ventilation when bathing or
showering and allow the fan to run until all the excessive moisture is vented from the
bathroom.
5. Resident shall use the exhaust fans in kitchen when cooking or while the dishwasher is
running and allows the fan to run until all excess moisture is vented from the kitchen.
6. When washing clothes in warm or hot water, Resident agrees to make sure condensation does
not build up within the washer and dryer closet; if condensation does accumulate, Resident
shall dry with a fan or towel.
7. Resident agrees not to overfill closets or storage areas. Ventilation is important in these spaces.
8. Resident agrees not to allow damp or moist stacks of clothes or other cloth materials to lie in
piles for an extended period of time.
9. Resident shall thoroughly dry any spills or pet urineon carpeting.
10. In damp or rainy weather conditions, Resident must keep windows and doors closed.
11. If possible, Resident shall maintain a temperature between 50- and 80-degrees Fahrenheit at all
times.
12. Resident shall clean and dust apartment home on a regular basis. Regular vacuuming,
mopping, and use of environmentally safe household cleaners are important to remove
household dirt and debris that contribute to mold growth.
13. Resident agrees to report immediately to the Landlord any evidence of water leak or
excessive moisture in the apartment home, storage room, garage or any common area, any
inoperable windows or doors or any musty odors that are noticed in the apartment home.
14. Resident agrees to report immediately to the Landlord any evidence of mold growth that can’t
be removed by simply applying a common household cleaner and wiping the area. Also,
Resident agrees to report any area of mold that reappears despite regular cleaning.
15. Resident agrees to report immediately to the management office any failure or malfunction
with the heating, ventilation and air-conditioning system (HVAC), or laundry system.
RESIDENT WILL NOT BLOCK OR COVER ANY OF THE HVAC DUCTS IN RESIDENTS
APARTMENT HOME.
NINETEENTH: BED BUGS: The parties acknowledge that bed bugs are almost always introduced to
an apartment by a human’s activities. They are usually introduced through personal items such as
luggage, purses, brief cases or furniture and other personal items brought into the apartment unit. The
Resident shall promptly advise the Landlord in the event that any bed bug infestation is discovered and
will cooperate as reasonably requested by the Landlord in preparation for treatment. To the degree that
the exterminator determines the Resident to be responsible for the infestation, the Resident shall be
obligated to pay the cost of remediation for Residents apartment and any apartments in the immediate
vicinity, IE barrier treatments in
surround units.
TWENTIETH: LIABILITY: Landlord shall not be liable for any damages or losses to person or property.
Landlord shall not be liable for personal injury or damage or loss to Resident's personal property
(furniture, jewelry, clothing, etc.) from theft, vandalism, fire, water, rain storms, smoke, explosions, sonic
booms, or other causes whatsoever, whether caused by negligent acts of Landlord, its agents or servants
or otherwise. Landlord RECOMMENDS that Resident secure insurance to cover risk of loss to
Resident's property. Landlord's property insurance does not cover risk of loss to any of Resident's
property. Also, if any of Landlord's employees are requested to render any services such as moving
automobiles, handling of furniture, cleaning, delivering packages, or any other service not required of
Landlord under this Agreement, such employee shall be deemed as an agent of Resident regardless of
whether or not payment is made by Resident for such service. Resident agrees to hold harmless and
indemnify and defend Landlord from any and all liability arising in any way whatsoever from the rendering
of such service. Resident must pay for damages suffered and money spent by us relating to any claim
arising from any act of Resident, Resident’s family, guests, and invitees.
TWENTY-FIRST: QUIET ENJOYMENT: Landlord agrees that on paying the Rent and Additional Rent
and performing the covenants herein contained, Resident shall peacefully and quietly have, hold, and
enjoy the Apartment Home for the agreed Lease Term. Quiet hours are from 10:00 pm to 8:00 am.
Notwithstanding any language to the contrary set forth herein, the Landlord shall have the absolute right,
at its sole discretion, to terminate the Lease Agreement without notice, for any conduct which the
Landlord considers objectionable. Such conduct may include, but is not limited to, threats or actual bodily
harm to Landlord’s staff members, property or bodily injury to any person thereon and/or to any violation
of the Rules and Regulations of Landlord set forth at paragraph twenty (20).

6
TWENTY-SECOND: MOTOR VEHICLES; PARKING:
1. Resident agrees to park at own risk. Landlord is not responsible for any damage made to any
vehicle parked in any of the designated parking lots/garages. Landlord reserves the right to make
rules for the use of all parking spaces; to place limitations upon use of parking spaces at any time
after the beginning of the term of this lease; to institute a reasonable charge for such use at any
time after the beginning of the term; and to make changes in the rules and charges from time to
time. Resident understands that if Landlord provides garage accommodations or assigns
reserved parking spaces, such garage accommodations or reserved parking spaces the charge
for such optional facilities may not be included in the apartment Rent. Garage accommodations
or reserved parking spaces may not be furnished to Resident unless a separate written
agreement is made between Landlord andResident.
2. To the extent Resident’s vehicle is not properly registered and/or licensed, or generally appears
to be in an inoperable condition (including, but not limited to, vehicles with flat or missing tires),
Landlord will provide written notice to Resident of such violations. To the extent the violations are
not corrected within twenty-four hours of receipt of written notice, Resident shall appoint Landlord
as Resident’s agent to have the vehicle towed from the property. However, non- compliance with
all other rules and regulations respecting parking shall entitle Landlord to have the vehicle towed
immediately, without notice, at owner’s risk and expense. In addition, if the vehicle is parked in a
manner which is dangerous, unlawful or which otherwise constitutes a nuisance or
inconvenience, Landlord may tow said vehicle immediately, without notice, at owner’s risk and
expense.
3. Landlord may modify the method by which parking is furnished at the apartment community or
billed to the Resident during the term of this Lease. Landlord may choose also to incorporate
assigned parking areas or eliminate any areas currently assigned. In the event Landlord chooses
to so modify parking on the apartment community, Landlord shall give Resident not less than
thirty (30) days prior written notice of such modification.
TWENTY-THIRD: NO WAIVER: Failure of Landlord to insist upon strict, timely compliance by Resident
with any term of this agreement shall not amount to nor be construed as nor otherwise constitute a waiver
by Landlord of Landlord's right thereafter to insist upon strict and timely compliance by Resident of any
and all terms and conditions of this agreement, including, without limitation, any term that may not have
been enforced strictly by the Landlord previously. Acceptance by the Landlord of Rent after knowledge
of any breach of this lease by the Resident shall not be a waiver of the Landlord's right nor construed as
an election by the Landlord not to enforce the provisions of this Lease pursuant to such a breach.
Landlord's failure or delay in demanding damage reimbursement, late payment charges, returned check
charges, or other sums due Landlord, shall not be a waiver of Landlord's right to insist on payment
thereof. Landlord may demand same at any time, including move-out or thereafter. The Resident hereby
waives Resident's right to demand a jury trial in any cause of action arising between Landlord and
Resident concerning this Lease Agreement.
TWENTY-FOURTH: INDEMNITY: Resident agrees to reimburse Landlord promptly for the cost to
Landlord for property damage to the Apartment and the common areas of the Community, including,
without limitation, the cost of repairs or service (including plumbing trouble) caused by Resident's
negligence, intentional acts and/or improper use by Resident, occupants, guests or invitees. Resident
shall be responsible for any such damage resulting from windows or doors left open. Payment of all
amount due Landlord under this provision or the agreement is due and payable within five (5) days of
delivery of written notice to Resident. All amounts due hereunder are deemed Additional Rent. Failure
of the Resident to pay for damages as required will be considered a material breach of this Lease
Agreement. Resident agrees to indemnify Landlord against, and to pay as Additional Rent, any claims
and expenses, including all attorney fees which Landlord may incur as a result of:
1. Theft, loss of use, or damage to any property of Landlords or anyone else’s by Resident
2. Bodily or any other injury to Resident, Resident’s family, guests, and Resident’s invitees by
Resident
3. Discharging a mechanic’s lien filed because of Resident’s failure to pay for labor or materials
4. RESIDENT’S ARE RECOMMENDED TO OBTAIN RENTER’S INSURANCE. Both parties
agree that Landlord shall not be responsible for the damage of Personal Property of Resident,
Resident’s family, guests, and Resident’s invitees.

TWENTY-FIFTH: EMINENT DOMAIN: Should the land where on the Apartment Home and the
Apartment Community are situated, or the major part thereof, be condemned for public use, then, in that
event, upon taking of the same for such public use, this Lease Agreement, at Landlord’s option shall be
null and void, and the term cease and come to an end, anything herein contained to the contrary
notwithstanding. Landlord will give written notice to Resident within sixty (60) days after such taking.

7
Landlord will have the sole right to any award or payment made on account of any taking or
condemnation, including buildings, appliances, appurtenances, or leaseholds.
TWENTY-SIXTH: SUBORDINATION AND NON-DISTURBANCE: This Lease Agreement shall be
subject and subordinate to any and all permanent or building loan mortgages covering the fee simple
interest of the real property and fixtures owned by Landlord, of which the Apartment Home and the
Apartment Community form a part, hereafter placed by Landlord, Landlord’s successors or assigns, and
to all advances made or to be made thereon, and all renewals, modifications consolidations,
replacements, or extension thereof, and the lien of any such mortgage or mortgages shall be superior
to all rights hereby or hereunder vested in Resident to the full extent of the principal sums secured
thereby and interest thereon, provided that each such mortgage existing or hereafter placed:
1. Shall provide by its terms that in the event of foreclosure of such mortgage, Resident shall remain
undisturbed under this Lease Agreement, so long as Resident complies with all of the terms and
conditions hereunder;and
2. Shall permit fire insurance proceeds payable under Landlords policies required by this Lease
Agreement to be used by Landlord.
This provision shall be self-operative and no further instrument or subordination shall be necessary to
effectuate such subordination; and the recording of such mortgage shall have preference and
precedence and be superior and prior in lien to this Lease Agreement, irrespective of the date of
recording, provided it contains the non-disturbance provisions of this paragraph.
TWENTY-SEVENTH: RESIDENT DEFAULTS AND LANDLORD REMEDIES:
1. Landlord may give three (3) days written notice to Resident to correct any of the following defaults:
a. Improper conduct by Resident, Resident’s family, guests or invitees or any other
occupant of the Apartment Home that Landlord may deem objectionable.
b. Misrepresentation of any material fact contained in the Resident’s Dwelling Application.
c. Resident’s failure to fully perform any other term of this Lease Agreement.
d. Resident’s failure to fully comply with the rules and regulations of the property.
2. If Resident fails to correct the defaults in Item 1 above within three (3) days following such
written notice, Landlord may cancel this Lease Agreement by giving Resident written notice
stating the date the Lease Agreement term will end. On that date Resident will vacate the
Apartment Home, return all keys and remove all personal belongings. Resident will be
responsible for:
a. Any and all damages to the Apartment Home.
b. Rent and Additional Rent through the end of the term of the Lease Agreement;
c. Utilities and other services through the end of the term of the Lease Agreement; and
d. Legal fees and costs associated with the termination of the Lease Agreement.
3. If the Lease Agreement is cancelled, or Rent or Additional Rent is not paid on time, or
Resident vacates the Apartment Home, Landlord may, in addition to other remedies,
take any of the following steps:
a. If Resident vacates or abandon the Apartment Home prior to the expiration of the
Lease Agreement term Landlord may enter the Apartment Home and remove any
remaining belongings;
b. Landlord may use eviction or other legal proceedings to recover possession of the Apartment
Home.
4. If the Lease Agreement is ended or Landlord recovers possession of the Apartment Home, all
Rent and Additional Rent for the unexpired term shall become due and payable. Landlord may
re-let the Apartment Home for a lower rent and give allowances to the new Resident. Resident
will be responsible for Landlord’s costs to include but not be limited to the cost of redecorating,
advertising, broker’s fees, attorney’s fees, and preparation of the Apartment Home for the new
Resident. Resident shall continue to be responsible for Rent, Additional Rent, expenses,
damages and losses during the balance of the term of the Lease Agreement. Any Rent
received from the new Resident will be applied to the reduction of money Resident owed.
Resident waives all rights to return to the Apartment Home after possession is given to
Landlord by a court.

TWENTY-EIGHTH: NO SECURITY SERVICES: The Landlord shall not provide nor does the Landlord
have any duty to provide security services for the protection of the Resident or the Resident's property.
The Resident hereby acknowledges the foregoing and agrees to look solely to the law enforcement
agencies of the county or municipality in which the Apartment is located for Resident’s protection. It is
agreed and understood that the Landlord shall not be liable to Resident for any damages, injuries or
wrongs sustained by others, or property of same from criminal or wrongful acts of Landlord, its
representatives, agents, employees, or any other persons or entities that may cause harm to Resident

8
resulting from a tortuous, criminal or wrongful act by same. In the event that the Landlord elects to hire
a security service to patrol or monitor the Apartment Community and common areas, it is understood
and agreed that said services are provided exclusively for the protection of the Landlord's property and
in no way whatsoever shall it be intended or construed as a waiver by the Landlord of the foregoing, nor
in any way whatsoever shall it be construed as creating a duty of the Landlord to protect the Resident.
TWENTY-NINTH: CORPORATIONS OR PARTNERSHIPS. If Resident is a corporation, company or a
partnership, the person signing this Lease on behalf of such corporation or partnership hereby warrants
that he/she has full authority from such corporation, company or partnership hereunder and said person
and the corporation, company or partnership shall be jointly and severally liable for all Rent and any and
all other amounts that may be due and owing to Landlord under the terms of this Lease, including
attorney’s fees and costs.
THIRTIETH: NO CONSTRUCTION LIENS: Resident shall have no power or authority to permit
construction, mechanics, material men’s or other liens to be placed upon the leased property in
connection with maintenance, alterations, and modifications or otherwise. The interest of the Landlord
shall not be subject to liens for improvements made by the Resident. Landlord shall not be liable for any
work, labor or materials furnished to the Premises by or through Resident or anyone claiming through
Resident. No construction liens or other liens for any such work, labor or materials shall attach or affect
the interest of the Landlord in and to the Premises. This lease itself shall not be recorded in the public
records.
THIRTY-FIRST: AMENITIES; RECREATION: Resident’s right to use any recreational
equipment/facilities that may be provided by Landlord shall be subject to any Rules and Regulations
posted regarding such equipment/facilities. Any amenity may be used only by Residents, Occupants
and their guests as outlined by the Rules and Regulations. Resident agrees that Resident is renting only
the Apartment. Rent does not include the use of any amenities, including recreational facilities, of the
Community. Landlord may from time-to-time issue new rules and regulations to govern the use of such
amenities. Such Rules and Regulations may call for the payment of fees, either on a seasonal, monthly
or annual basis, for membership. Fees for use by Resident guests of the amenities may be charged.
The use of any amenity may be allowed or revoked in Landlord’s sole discretion. The amenity may be
removed from service by us on a permanent or part-time basis without compensating Resident and Rent
may not be withheld nor the lease terminated based on such action.
THIRTY-SECOND: BANKRUPTCY: If Resident assigns the leased Apartment Home for the benefit of
creditors, or Resident files a voluntary or an involuntary petition is filed against Resident under any
bankruptcy or insolvency laws or a trustee or receiver is appointed, Landlord may give Resident thirty
(30) days’ notice of cancellation of the term of this Lease Agreement. If any of the action(s) is/are not
fully dismissed within the thirty (30) days, the Term shall end as of the date stated in the notice. Resident
must continue to pay Rent, Additional Rent, damages, losses and expenses without offset.
THIRTY-THIRD: CARPET/FLOORING CLAUSE: Resident agrees that Resident will exercise diligent
care and caution in the treatment and use of any carpeting/flooring and will maintain and clean the
carpeting/flooring according to the manufacturer’s recommendations. Resident agrees that Resident will
be responsible for any damage to the carpeting/flooring (reasonable wear and tear under ordinary usage
expected).
THIRTY-FOURTH: WAIVER OF JURY, COUNTERCLAIM SETOFF: Resident and Landlord waive the
right to a jury trial in any dispute between the parties under this Lease Agreement (except for a personal
injury or property damage claim). In proceeding to obtain possession of the Apartment Home, Resident
shall not have the right to make a counterclaim or set-off.
THIRTY-FIFTH: PARTIAL INVALIDITY: If a court deems any part of this Lease Agreement invalid or
illegal, then only that part shall be void and it shall have no other effect on the remaining terms and
conditions of this Lease Agreement. All other terms and conditions of this Lease Agreement shall remain
in full force and effect.
THIRTY-SIXTH: PERSONS BOUND BY LEASE; JOINT AND SEVERAL LIABILITY: Residents agree
(if there are more than one signatory to the Lease Agreement) that the Lease Agreement may be renewed
upon the signature of any one of Resident, and shall be binding upon each individual as if each and all
of Residents signed the renewal. Resident further agrees that delivery to any one of the Residents shall
be deemed delivered to each and all of the Residents. This Lease Agreement may be signed in
counterparts and the combined Lease Agreement shall be binding as if all signatures were on one Lease
Agreement. This Lease Agreement shall be binding on us and Resident and any parties that may

9
succeed in their interest. Resident’s liability under the Lease Agreement shall be joint and several for
Rent, Additional Rent, damages or any other debts or charges including but not limited to attorney’s fees
or collection action fees incurred by virtue of the Lease Agreement.
THIRTY-SEVENTH: REPRESENTATIONS: Resident agrees that Resident has read and understand
this Lease Agreement. All promises are contained herein and there are no other agreements.
THIRTY-EIGHTH: EFFECTIVE DATE: The Lease Agreement is effective when signed by all parties.
Lease may not be canceled after signed.
THIRTY-NINTH: HOLD HARMLESS: Resident shall indemnify Landlord against, and save Landlord
harmless from and reimburse Landlord for any and all damages, expenses, fines or penalties, injury or
liability to any person or persons or property occasioned wholly or in part by any act or omission of
Resident, Resident’s family, guests, and Resident’s invitees and Resident releases Landlord and
Landlord’s employees and agents from all liability for any damages or bodily injury resulting from the
action of others who may enter the Apartment Home illegally or with criminal intent and Resident agree
to hold us harmless for any injuries, harm or damages resulting there from.
FORTIETH: MODIFICATION OR CHANGE OF LEASE AGREEMENT: No oral changes may be made
to the Lease Agreement or any attachments or addenda to the Lease Agreement. All changes must be
in writing.
FORTY-FIRST: OUR INABILITY TO PERFORM: If due to labor trouble, government order, lack of
supply, Resident’s act or neglect, or any other cause not fully within Landlord’s reasonable control,
this Lease Agreement shall not be ended nor Resident obligations be affected if Landlord cannot
carry out any of Landlord’s promises or agreements contained in this Lease Agreement.
FORTY-SECOND: LANDLORD: The term “Landlord” as used in this Lease Agreement means the
owner, agents or the mortgagee in possession for the time being of the land or the building (or the owner
of a lease of the building or of the land and building) of which the Apartment Home forms a part, so that
in the event of any sale or sales of said land and building or of said lease, or in the event of a lease of
said building or of the land and building, Landlord shall be and thereby are entirely free, and relieved of,
all covenants and obligations.
FORTY-THIRD: PERSONAL PROPERTY: BY SIGNING THIS RENTAL AGREEMENT, THE
RESIDENT AGREES THAT UPON SURRENDER, ABANDONMENT, OR RECOVERY OF
POSSESSION OF THE DWELLING UNIT DUE TO THE DEATH OF THE LAST REMAINING
RESIDENT, THE LANDLORD SHALL NOT BE LIABLE OR RESPONSIBLE FOR STORAGE OR
DISPOSITION OF THE RESIDENT’S PERSONAL PROPERTY.
FORTY-FOURTH: END OF TERM: Resident will remove all of Resident’s property and belongings at
the end of the term of this Lease Agreement. Resident will leave the Apartment Home in clean condition
and in good repair. Resident will restore unit to original state upon move out. Resident shall pay any
damage to the Apartment Home, building, or grounds caused by Resident by moving. If Resident leaves
any personal belongings in the Apartment Home, Landlord may dispose of it and charge Resident for
the costs of disposal pursuant to the terms contained in the Schedule of Minimum Charges (Addendum
4) of this Lease Agreement or keep it as abandoned property. Resident shall be responsible for all Rent
and Additional Rent until the expiration date of the Lease Agreement.
If Resident remains in possession of the Apartment Home after the end of the Lease Agreement term
without Landlords prior written consent, then Landlord may:
1. Commence summary proceedings to dispossess Resident;
2. Declare Resident a holdover Resident at a new rental term on a month-to-month basis. The
month-to-month term shall begin on the first day after the expiration of the current Lease
Agreement. All provisions of this Lease Agreement shall apply to the month-to-month rental
term except that Rent payable hereunder shall be increased to the going market rent, in
addition the rent will be increased by One Hundred Dollars ($100.00) per month plus any
Additional Rent charges that may be incurred by Resident;

FORTY-FIFTH: ADDENDA: Resident certifies that Resident has received a copy of this Lease
Agreement and the following addenda to this Lease Agreement and that Resident understands that
all addenda become a part of the Lease Agreement:

10
POLICY AND REGULATION ACCEPTANCE RESIDENT(S)
ADDENDUM NO 1 – RENT PAYMENT POLICY
ADDENDUM NO 2 – RULES AND REGULATIONS
ADDENDUM NO 3 – APARTMENT INSPECTION REPORT
ADDENDUM NO 4 – SCHEDULE OF MINUMUM CHARGES ADDENDUM
ADDENDUM NO 5 – PET AGREEMENT
ADDENDUM NO 6 – LEAD PAINT ADDENDUM
ADDENDUM NO 7 – PARKING LEASE NA
ADDENDUM NO 8 – GUARANTY OF PAYMENT NA
ADDENDUM NO 9 - UTILITIES
ADDENDUM NO 10 – FITNESS CENTER / AMENITIES NA
ADDENDUM NO 11 – CONCESSION ADDENDUM NA
ADDENDUM NO 12 – SMOKE-FREE COMMUNITY
ADDENDUM NO 13 – OPERATION OF POOL AND RULES NA

IN WITNESS WHEREOF, the parties have executed these the day and year first above written. Resident
signature indicates they have read the entire agreement including the terms and conditions set forth
above.

Residents: Date: Witnesses: Date:
7/20/2023 7/20/2023

RESIDENT’S INITIALS

11

ADDENDUM NO. 1
RENT PAYMENT
POLICY

The Resident agrees to pay to Landlord in advance at the commencement date of this Lease and
thereafter on the first day of each and every consecutive calendar month thereafter, by personal check,
money order, cashier's check or through the online payment portal, the monthly rental amount set forth
hereinabove. It is agreed that at no time shall cash be accepted by Landlord for payment of Rent.
Landlord shall not accept payment of Rent from a non-Resident. For purposes of this Lease Agreement
it shall be irrefutably presumed that Resident has not paid rent unless Resident can produce a canceled
check or money order purporting to prove Rent has been paid to Landlord. If this Lease commences on
a date other than the first day of the month, the Resident shall be responsible for paying Landlord a
prorated amount of said rent based upon the actual number of days in the first month of the tenancy that
Resident occupied the Apartment. This amount shall be payable in advance to Landlord. All late fees
and returned or dishonored check fees shall be deemed as Additional Rent for the purposes of this
Agreement. Landlord may proceed with an action for possession and breach of contract at the expiration
of the Fourteen Day Notice. If Resident will be absent from the premises for more than fourteen days,
Resident must notify Landlord in writing.
The following policy has been instituted to protect the status of quality, responsible Residents. Landlord
believes that those individuals who meet their financial obligations on a timely basis – permit Landlord
to meet Landlord’s financial obligations – should not be penalized in the form of higher rents due to
delinquent payment practices of their fellow Residents.
This Rent Payment Policy is a rider to and forms a part of the Lease Agreement between Landlord
and Resident, as noted on Page 1 of the Lease Agreement. It is expected that there will be no
collection problems. The policies and procedures that follow will apply in those situations when a
delinquency occurs.
1. Resident agrees and understands that Rent and Additional Rent payments are due and payable
on or before the 1st day of each and every month, regardless of weekends and/or holidays.
2. All rental payments during the Rental Term shall be payable to: Ishan Chhabra.
3. Landlord need not give notice to Resident to pay Rent or Additional Rent.
4. A courtesy period is provided to allow for unusual (non-recurring) circumstances. All payments
must be received by Landlord no later than 5:00 PM on the fifth (5th) day of the month, regardless
of weekends and/or holidays.
5. Payments that arrive after 5:00 PM on the fifth (5th) of the month will be late. Failure to make
Resident payment in full within the courtesy period will cause Resident to incur a late fee of 5% or
$50, whichever is less, which is due and payable immediately with Resident Rent payment.
6. To ensure proper credit all payments must note Residents Apartment number.
7. Landlord has the right to apply all monies received as Landlord deems appropriate to pay Resident
obligations due Landlord.
8. Landlord may accept any partial payment with any conditional endorsement without prejudice
to Landlord’s right to recover the balance remaining due, or to pursue any other remedy
available under this LeaseAgreement.
9. Resident may be required to pay additional charges under the terms of this Lease Agreement.
These additional charges are deemed “Additional Rent” and shall be due pursuant to the terms
of this Lease Agreement. If Resident fails to pay Additional Rent on time or on demand, Landlord
shall have the same rights against Resident as if it were a failure to pay Rent. Additional Rent
shall include but is not limited to any charges levied by Landlord during the term of this Lease

RESIDENT’S INITIALS

12
Agreement.
10. Any payment presented to us that is not honored shall result in Landlord charging Resident ANY
bank fee assessed, PLUS an amount of 5% or $50, whichever is less, as a late fee, PLUS an
amount of not less than Thirty-Five Dollars ($35) as an insufficient funds (NSF) fee. All such sums
shall constitute Additional Rent. Landlord also reserves the right to pursue any criminal and civil
charges against Resident under all applicable local, state and federal statutes. Thereafter,
Landlord will require that all future payments MUST be made by money order, certified check,
bank check or other immediately available funds. If more than 2 payments are returned insufficient
funds (NSF), Resident will be required to pay in certified funds ONLY and will have their online
payment option revoked.
11. Resident accepts and understands that on or about the sixth (6th) day of the month a statutory
five-day notice will be issued to Resident if Landlord does not receive full payment. Failure to

make full payment of all sums due within the five (5)-day notice period will then have a Fourteen-
day notice issued, If rent is not paid in the Fourteen-day notice period, commencement of a

Summary Proceeding (eviction action) against Resident, which will seek a warrant of eviction and
a monetary judgment.
12. In the event of Resident death during the term of this Lease Agreement, Residents estate shall
remain liable for the payment of Rent and Additional Rent as per the Rent Payment Policy of
this Lease Agreement.

RESIDENT’S INITIALS

13

ADDENDUM NO. 2

RULES AND REGULATIONS
1) The sidewalks, entrances, passages, breezeways, courts, stairways, corridors and halls must
not be obstructed or encumbered, may not be used for the storage personal items or for any
purposes other than entering and leaving the Apartment Home.
2) No sign, advertisement, notice or other lettering shall be exhibited, inscribed, painted or affixed by
Resident on any part of the outside or inside of the Apartment Home or within the Apartment
Community without Our prior written consent.
3) Carriages, tricycles, bicycles or any other similar articles are not allowed in hallways,
passageways, breezeways or courts of the buildings; nor may such articles be chained to any part
of the Apartment Home or Apartment Community or railings, fences or fire escapes, or left
obstructing sidewalks.
4) Playing or congregating in the common halls, stairways or breezeways or any of the exterior
landscaped areas is prohibited.
5) Landlord’s laundry equipment shall be used in such manner and at such times as Landlord may
direct. Resident shall not dry or air laundry, towels, rugs, etc. on the roof, balcony, patio, terrace,
stairways or interior railings.
6) Resident shall not allow anything whatever to fall from the windows or doors of the Apartment
Home or the Apartment Community, nor sweep or throw from Resident’s Apartment Home any
dirt or other substance into the halls or common areas of the Apartment Community.
7) No garbage cans, mats or other articles shall be placed in the halls or on the staircase landings,
nor shall anything be hung from the window, terraces or balconies or be placed upon the
windowsills that may degrade the appearance of the building. No awnings, antennas or other
projections shall be attached to the outside of the building of which the apartment is a part of.
8) Resident, Resident’s family members, agents or visitors shall not make or permit any disturbing
noises in the building, nor do or permit anything that will interfere with the rights, comforts or
convenience of other Residents. Resident shall not play or allow to be played, any musical
instrument or operate or allow to be operated a vacuum cleaner, stereo, television or radio in the
Apartment Home between the hours of 10 p.m. and 8 a.m., if the same shall disturb or annoy
other occupants of the building. Resident shall not give vocal or instrumental instruction in the
Apartment Home at any time.
9) The water-closets and other plumbing fixtures shall not be used for any purposes other than
those for which they were constructed, nor shall any sanitary products, sweepings, rubbish, rags,
or any other improper articles be thrown into same. The cost of repairing any damage resulting
from the misuse thereof shall be borne by Resident.
10)Resident shall reimburse or compensate Landlord for any damage or injuries to trees, lawns,
shrubs, and plants in the Apartment Community caused by Resident, Resident’s family
members, employees, agents orguests.
11)Resident, Resident’s families, friends and agents will obey the parking and traffic regulations
posted at the private streets, roads and drives.
12)No motorcycles, mini-bikes or other gas-operated equipment are permitted to be placed within
ten feet of the buildings; nor may any charcoal lighter or propane grills be left within or used
within ten feet (10’) of buildings.
13)If Resident is expect to be away for longer than 24 hours and plan to leave Resident’s car on the
premises, Resident must notify us who to contact to move Resident’s vehicle in the event of an
emergency or in the event of snow removal, November through March.

RESIDENT’S INITIALS

14
14)Walls and wall coverings are not to be altered by Resident without Landlords prior written approval.
15)Appliances should be properly cared for; grease buildup should be prevented on range top and in
ovens; and frost build- up in the freezer compartment of the refrigerator. When defrosting, DO
NOT use any type of sharp instrument to scrape off the ice as it may puncture the refrigerant coil.
Any damage caused by Resident to any of Landlord’s equipment will be charged to Resident as
Additional Rent.
16)Resident at Resident’s expense shall complete snow removal from Residents exclusive use area
of the Apartment Home. Exclusive use area is defined as those areas to which Residents have
control and access to and from Resident’s Apartment Home and no other common area of the
Apartment Community. Landlord will remove snow from all common areas of the Apartment
Community.
17)Resident agrees to:
a) Keep the Apartment Home clean and sanitary;
b) Use all appliances, fixtures and equipment in a safe manner and only for the purposes and in
the manner for which they are intended;
c) Not litter the grounds or common areas of the Apartment Community;
d) Not destroy, deface, damage or remove any part of the Apartment Home, common areas or
Apartment Communities grounds;
e) Not use any open flame products that might cause a fire to occur;
f) Give us prompt notice of any defects in plumbing, fixtures, appliances, heating or cooling
equipment or any other part of the Apartment Home or related facilities;
g) Remove garbage and other waste from the Apartment Home in a clean and safe manner
and dispose of it in the designated method;
h) To fully cooperate with us to achieve compliance with requirements for waste separation and
recycling;
i) Not leave children unsupervised;
j) Not disturb the peaceable occupancy of others;
k) Not give keys to individuals not residing in the Apartment Home without Landlords prior written
approval; and
l) Not create any conditions within the Apartment Community that pose a threat to the health or
safety of any person or persons.
18)Deck, Balcony or Patio Storage and Use
a) Maintenance. Resident shall keep the Deck, Balcony or Patio neat and clean at all times.
b) Storage. No flowerpots, planters or other objects may be placed or stored on Deck, Balcony,
Patio Railings or Entryways. Only outdoor patio furniture may be kept on Deck, Balcony or
Patio. No storage of any kind is permitted, including but not limited to, recyclables; garbage;
interior furniture; toys; housekeeping tools; machinery; or recreational, exercise or other
equipment. Resident shall not keep combustible or flammable goods or materials on Deck,
Balcony or Patio, including, but not limited to, propane grills, tanks, charcoal, lighter fluid, paint,
cleaning solutions, gasoline, firewood, and newspapers. No rugs, towels, laundry, clothing,
clotheslines, or other items shall be stored or hung on the deck or draped over Deck, Balcony
or Patio railings.
c) Outdoor Cooking. Outdoor cooking is prohibited on Resident’s Balcony. Resident may not
use or store any gas, charcoal, or other type of cooking appliance or grill on Resident’s
Balcony. Outdoor cooking is allowed in the grass areas, but not the landscape planting beds,
of the Apartment Community, provided Resident is not closer than ten feet (10’) to any of the
buildings located within the Apartment Community AND Resident does not allow the fire or
smoke to bother any other Resident.
d) Safety. Residents shall not toss or throw any object from the Deck, Balcony or Patio.
e) Pets. Pets are not permitted on the Deck, Balcony or Patio.
f) Right of access. In the event Resident store materials or items on the Deck, Balcony or Patio
that Landlord deem hazardous to the safety of the Apartment Community or other Residents,
Landlord reserve the right to remove and store such items at Resident’s expense.
19)Refuse & Recycling
a) Resident agrees, at Resident’s sole expense, to comply with all present and future laws and
regulations of state, federal municipal and local governments, departments, commissions

RESIDENT’S INITIALS

15
and boards regarding the collection, sorting, separation, and recycling of waste products,
garbage, refuse and trash. Resident will sort and separate all such items into categories as
provided by law and in accordance with the rules and regulations adopted by Landlord for the
sorting and separating of such designated recyclable materials.
b) If Resident fails to comply with the rules and regulations, Landlord reserves the right, where
permitted by law, to refuse to collect or accept from Resident any waste products, garbage,
refuse or trash that is not separated and sorted as required by law, and to require Resident to
arrange for such collection, at Resident’s sole expense, using a contractor satisfactory to
Landlord.
c) Resident will pay all costs, expenses, fines, penalties or damages imposed on us or Resident
by reason of Resident’s failure to comply with paragraphs a) and b) above. Resident also will
hold us harmless from any actions, claims and suits arising from Resident’s noncompliance.
Resident’s noncompliance with paragraphs a) and b) above will constitute a substantial
breach of the Lease Agreement.
d) To ensure cleanliness and sanitary conditions, all loose refuse or trash must be wrapped tightly
before being put into the trash containers. All trash must be placed inside the trash containers.
20)In consideration of the execution of the Lease Agreement, or any renewal thereof, Resident agree as
follows:
a) Resident, Resident’s family, guests, and Resident’s invitees will not engage in any criminal
activity including but not limited to drug related activity anywhere within the Apartment
Community, including but not limited to Resident’s Apartment Home.
b) “Drug Related or Criminal Activity” means the manufacture, sale, distribution, use or
possession with the intent to manufacture, sell, distribute or use a controlled substance as
defined in Section 102 of the Controlled Substance Act (21 U.S.C. 802).
c) Resident, any member of the Resident’s household, a guest or other person affiliated in any
way with the Resident, shall not engage in any illegal activity including prostitution, criminal
street gang activity, threats or intimidation, assault, including, but not limited to the unlawful
possession or discharge of Firearms or illegal weapons on or near the premises, or any other
violation of the criminal statutes or any breach of the Lease Agreement that otherwise
jeopardizes the health, safety and welfare of the Landlord, their agent, other Residents, or
guests or that which involves imminent or actual serious property damage. Resident,
Resident’s family, guests, and Resident’s invitees will not permit nor allow the Apartment
Home to be used for Criminal Activity, regardless of whether Resident, Resident’s family,
guests and Resident’s invitees engage in such activity.
d) A violation of this Section constitutes a substantial violation of the lease and a material
noncompliance with the lease for which the Resident shall not be given the opportunity to cure.
Any such violation is grounds for termination of tenancy and eviction from the unit.
e) Resident represents that neither Resident nor any occupant of the Apartment has ever been
convicted of any felony or misdemeanor involving sexual misconduct or controlled substance,
and that to the best of Resident’s knowledge, neither Resident nor any occupant of the
apartment is the subject of a criminal investigation or arrest warrant. Resident hereby further
represents that neither Resident nor any occupant of Resident’s apartment has any criminal
charges of a sexual nature pending adjudication at this time. Resident agrees that Landlord
may terminate this lease if it ever comes to the attention of the Landlord that Resident
has been convicted of any sexual criminal activity or placed on probation with
adjudication withheld at any time prior to becoming a Resident or during Resident’s
tenancy at the apartment community. Resident authorizes Landlord to perform a criminal
background investigation of the Resident or any occupant of the apartment in the event the
Landlord, in its sole discretion, has reason to believe that the Resident or any occupant has
engaged in or is engaging in criminal activity in the apartment or at the apartment community.
f) In case of a conflict between the provisions of this section and any other section of the
Lease Agreement, the provisions of this section will govern.
21)Resident agrees and understands:
a) The smoke detector(s) and carbon monoxide detector were checked and are in operable
condition at the time of this Lease Agreement.
b) Resident is responsible for all maintenance and replacement of all smoke detector and
carbon monoxide detector batteries.
c) Resident is required to test the smoke detector(s) and carbon monoxide detector at least once
a month (pressing the “TEST” button to check for the appropriate audible or visual signal).
d) Resident will not disable the smoke detector(s) or carbon monoxide detector at any time.

RESIDENT’S INITIALS

16
e) If a fire should occur, and it is determined that Resident, Resident’s family, guests, and
Resident’s invitees have tampered or disabled the smoke detector in any way, that Resident
is liable to Landlord for any and all damages of any sort.
f) If a carbon monoxide leak is detected, and it is determined that Resident, Resident’s family,
guests, and Resident’s invitees have tampered or disabled the carbon monoxide detector in
any way, that Resident is liable to us for any and all damages of any sort.
g) If the smoke detector(s) or carbon monoxide detector is missing or broken upon termination of
the Lease Agreement Resident will be charged replacement and installation cost.
22)Resident shall not keep or have on the Apartment Community or in the Apartment Home any
article or thing of a dangerous, combustible, or explosive character that might unreasonably
increase the danger of fire on the Apartment Community or in the Apartment Home or that
might be considered hazardous or by Landlord or any responsible insurance company.
23)Resident shall make no changes or additions to the electrical wiring as installed and maintained
by Landlord, nor shall Resident install and/or operate any air conditioning equipment, clothes
washing or drying machine, electric broilers, space heaters of any kind, dishwashing machines,
electric stoves or ranges, freezing units and any other electrical equipment and/or appliances not
furnished by Landlord without Landlord’s prior expressed written consent.
24)If Landlord does not provide window treatments then Resident shall be responsible for covering
windows in Residents Apartment Home with white backed window coverings of suitable design
such as drapes, curtains or blinds. In no event shall Resident be allowed to utilize blankets,
towels, sheets, newspapers, paper or other similar unconventional window coverings. If Resident
does not comply with this provision, Resident shall be charged as Additional Rent, a minimum of
twenty-five dollars ($25) per day, commencing five (5) days after a written violation notice has
been delivered to Resident.
25)Any personal property of Residents not properly kept or stored, when not in actual use by
Resident, in Resident’s Apartment or in Resident’s private assigned storage area, will be
removed at Resident’s expense.
26)Unless prohibited by statute or otherwise stated in the Lease, Landlord may conduct
extermination operations in Residents apartment several times a year and as needed to prevent
insect infestation. Landlord will notify Resident in advance of extermination in Resident’s
Apartment and give Resident instructions for the preparation of the Apartment and safe contact
with insecticides. Residents will be responsible to prepare Resident’s Apartment for
extermination in accordance with Landlord’s instructions. If Residents are unprepared for a
scheduled treatment date Landlord will prepare Resident’s Apartment and charge Resident
accordingly.
27)Resident will not have water beds or other water furniture in the apartment without prior written
permission from Landlord and proof of renters’ insurance.
28)Resident agrees to keep the Apartment Home and the fixtures in it in good condition. Resident
also agrees to make all minor repairs that are made necessary because of the fault of Resident,
Resident’s family, guests, and Resident’s invitees. If Resident fails to make a needed repair,
Landlord may do it at Resident’s expense; such expense shall then be charged to Resident as
Additional Rent.
29)Resident shall not alter or replace locks or knockers or other attachments upon any door.
30)Resident shall not paint or apply any adhesive type of paper/product on the walls, cupboards,
windows, etc. without the Landlord’s written approval.
31)Resident, Resident’s family, friends and visitors shall not speed throughout the community and will
obey posted speed limit signs.
32)Resident agrees not to use attic space in the upper level apartments for additional storage.
33)Solicitation by flyer, note or other means is notpermitted.
34)Resident shall not interfere with management in the performance of their duties, nor shall Resident

RESIDENT’S INITIALS

17
make any threats to any management personnel. Violation of this provision shall be considered a
material breach of the lease entitling Landlord to terminate the Resident’s right of occupancy
immediately.
35)If Resident(s) leave the windows of the apartment open when the air temperature is below 55
degrees, a reasonable charge will be accessed to the rent on a prorated basis for the increased utility
usage.
36)Landlord will provide window coverings, however if window coverings are damaged Resident is
responsible for the cost in damages.

RESIDENT’S INITIALS

18

ADDENDUM NO. 3

MOVE IN/MOVE OUT CHECKLIST

TENANT NAME(S):

Crossland Beer
Leticia Losey

Address & Apt. No.: City State Zip
Condition on Arrival Condition on Departure Estimated Cost of
Repair/Replacement

LIVING
ROOM/BEDROOM
Flooring
Doors & Locks
Windows/Walls
Ceiling
Light
Fixtures
KITCHEN
Flooring
Doors/Walls/Windows/Ceilings
Light
Fixtures
Counters/Drawers/Cabinets
Microwave/Range Hood
Stove/Oven
Refrigerator
Dishwasher
Garbage Disposal
Sink & Plumbing
BATHROOM
Flooring
Walls & Ceilings
Tub/Shower/Toilet
Windows & Doors
OTHER

MOVE-IN MOVE-OUT
Date: Signature: / Date:
Date: Signature: / Date:
I/We (the tenant(s)) understand that unless otherwise noted, all discrepancies will be the tenant's responsibility and will
be deducted from the security deposit at the time of move-out.
MOVE-IN MOVE-OUT
Date: Date:
Landlord/Agent Signature Landlord/Agent Signature

RESIDENT’S INITIALS

17

ADDENDUM NO. 4

SCHEDULE OF MINIMUM CHARGES

Item Minimum Charge
Kitchen
1. Stove/Hood
Cleaning $50
Drip pan replacement $5 each
2. Refrigerator
Cleaning $75
3. Drawers/Cupboards/Cabinets
Emptied $2 each
Missing hardware Parts plus labor
Damaged Replacement cost plus labor
Cleaning $3 each
4. Microwave
Cleaning $45
5. Disposal
Cleaning $20

Appliance Replacement/Parts replacement Replacement cost plus $75
Bathroom

Broken light Fixtures Parts plus labor
Damaged cabinets & countertops Parts plus labor
Cleaning – Bathtub/tiles $40
Cleaning – Floors $30
Cleaning – Sink/toilet $40

Walls

Crayon/Ink/Sticker removal $35 per hour per technician
Holes $35 per hour per technician
Unauthorized wall coverings $35 per hour per technician
**Where tenant has repainted without permission and wall cannot be covered in one coat, an extra $40 charge per wall will be
made. All walls must be wiped clean and dust free, including baseboards & ledges.
Bedrooms

Walk-in doors $85 each
Closet doors $90 each

Ceilings

Holes or damage $35 per hour per technician

Flooring

Refinishing Parts plus labor
Mopped/vacuumed $20 per room
Stains/spots Replacement cost

Windows/Doors

Cleaning $15 per window
Replacement or glass or door Replacement cost plus $75

Trash Removal $20 per bag
Keys

Fob $50
Apartment key $10
Mailbox key $15
Door lock change $80
Mailbox Lock change $60

Paint

Repaint $300
Clean walls $35 per wall
Maintenance hourly rate on misc. repairs $89

RESIDENT’S INITIALS

18

ADDENDUM NO. 5
PET AGREEMENT

Please initial one box below:

I have a pet at this time.
I do not have a pet at this time.

Permissible Pets: Dog Cats Other Permitted Pets (as defined below) _ NO Pets
of any kind
If this page is applicable, Resident agrees to the following terms and conditions:
1. All Pets MUST be spayed or neutered. Proof of spaying or neutering is required. Possession of
any Pet not spayed or neutered will be considered a breach of the Lease Agreement and will result in
the assessment of a $500.00 charge which shall be considered Additional Rent.
2. Pet limitations – Max One (1) dog that are not an aggressive breed or one (1) cat. Max one (1)
pet per unit if allowed.
3. Only the pet(s) listed and described below is/are authorized under this Pet Agreement.
Landlord must approve all additional or replacement pets.
4. This Pet Agreement is part of the Lease Agreement between Resident and Landlord. If any
rule or provision of this Pet Agreement is violated, Landlord shall have the right to cancel Residents
Lease Agreement. Any refusal by Resident to immediately comply with such demand shall be
deemed to be a material breach of the Lease, in which event Landlord shall be entitled to all the
rights and remedies set forth in the Lease Agreement for violations thereof, including but not limited
to eviction, damages, and attorney’s fees.
5. Pet(s) may not cause a danger, damage, nuisance, noise or health hazard; or soil the unit,
premises, grounds, common areas, walks, parking areas, landscaping or gardens. Resident shall be
strictly liable for any damages for wrongful death, or injury to the person or property of others, caused
by Pet, and Resident shall indemnify us for all costs resulting from it.
6. Resident agrees to register the pet(s) in accordance with local laws and requirements.
Resident further agrees to immunize the pet(s) in accordance with local laws and requirements.
Resident agrees to maintain such licensing and inoculation of the pet and to furnish evidence thereof
promptly, upon request. It is solely the Residents medical and financial responsibility in the event of a
pet bite or other injuries to another person.
7. Resident warrants that the pet(s) is(are) housebroken. Resident further warrants that the
pet(s) has no history of causing physical harm to persons or property, such as biting, scratching,
chewing, etc., and further warrant that the pet(s) has(have) no vicious history or tendencies.
8. Resident acknowledges and agrees that Landlord may, at any time and in Landlords sole
and absolute discretion, revoke Landlords consent for Resident to keep pet. Landlord may revoke
consent if Landlord receives complaints from neighbors or other Residents about Residents pet, or
if Landlord, in sole discretion, determines that Residents pet has disturbed the rights, comfort,
convenience, or safety of neighbors or other Residents. Resident shall immediately and
permanently remove Residents pet from the Apartment Community upon Landlords written notice
that consent is revoked.
9. Any animal commonly kept as a household pet, such as a domesticated cat, or dog shall be
defined as a common household pet. Other permitted pets shall be fish (one tank, 10 gallons or less
only), caged and/or confined animals to include gerbils, hamsters, guinea pigs and turtles. Reptiles
(other than turtles) are prohibited. There is a limit of two common household pets per apartment.
These pets must be registered with Leasing Office. Any pets described above found in any apartment

RESIDENT’S INITIALS

19
home are subject to a $500 fee. Landlord reserve the right to refuse to register a pet if the pet is not a
common household pet or if it is known for damaging property.
10. Visiting Pets are not permitted any time.
11. Service animals and emotional support animals are not considered pets. There is no size or
weight limit for service animals or emotional support animals nor is there a pet fee or deposit required,
although information on the animal, including a picture, must be provided to Landlord, along with
proper documentation, such as note from a licensed medical professional.
12. Dogs and Cats shall not be out on the Apartment Community at any time unless on a short
leash and under Residents direct control. Resident shall not tie pet to any object outside Residents
Apartment Home or within the Apartment Community. Barking will not be tolerated in that it is
considered to be a nuisance to other Residents. Resident agrees to clean up after pet(s). Proper
disposal of pet feces (securely bagged) will be done each and every time the pet defecates. Failure
to do so will result in a $25.00 clean-up fee.
13. Odors arising from Residents pets will not be permitted.
14. Birds will be properly caged. Seeds and droppings will be shielded or caught to prevent
accumulation and/or damage to carpeting/floors.
15. Aquariums will not leak and will be cleaned regularly to prevent foul water and/or odors.
16. Any breach of any provision in this Addendum will result in an immediate $500 fee which will
constitute Additional Rent and shall be payable within 72 hours following receipt of written notice of
violation.

"""

    
    
    """
You are LoanGPT. Your goal is to be a knowledgable and kind guide for those who do not know much about loans.

You should pull from all your existing knowledge about loans and their related financial components. 

Your reponses should be well thought out. You should think in a step by step manner. You should be sure to justify your reasoning and provide context for those who know less about loans. 
"""

    messages = [
        {'role':'system', 'content':startupMsg},
        {'role':'user', 'content':lease},
        #{'role':'user', 'content':'Please read the terms of my lease above. Does this seem like normal landlord practice in new york?'},
        {'role':'user', 'content':'Please read the terms of my lease above. Does this seem like normal landlord practice in new york? Do any parts stand out as being shady or illegal?'},
        {'role':'assistant', 'content':'I am ready to assist you with any financial queries!'},
    ]

    chat = Chatter('gpt-3.5-turbo-16k') 
    chat.chat(include_previous_replies=True, extra_messages=messages)

