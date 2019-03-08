"""
file: mainbot.py
author: sanad(https://github.com/mohdsanadzakirizvi)
desc: contains primary code of the bot
license: MIT
"""
import slack_utility
import time
import os

# Import sqlite3
import sqlite3
from grammar_response import res_grammar

# Rasa NLU codes
from rasa_nlu.training_data import load_data
training_data = load_data("grammar_based_data5.json") 
from rasa_nlu.config import RasaNLUModelConfig
from rasa_nlu.model import Trainer 
config = RasaNLUModelConfig(configuration_values= {'pipeline': 'spacy_sklearn'}) 
trainer = Trainer(config) 
interpreter = trainer.train(training_data)

# create dictionaries and lists for later use

# the list of intents used 
intents_list = ["greet", "goodbye", "hotel_search", "grammar", "affirm", "rest", "reject"]

# there are some subtopics that are more comprehensive, which are tagged also as topics. for instance, when
# a user asks "can you talk about nouns, in particular countable nouns?", it is more important to retrieve data
# about countable nouns. therefore we'll use this list to differentiate between subtopics
topic_list = ['noun','nouns','pronoun','pronouns','adjective','adjectives','adverb','adverbs','determiner',\
 'determiners','verb','verbs','relative clause','relative clauses']

# a dictionary to map intents to entities. this is required since sometimes the interpreter can assign entities 
# belonging to intents that are not associated with a given user message (e.g. although "hotel_search" is assigned
# as the intent to the user message "hotel in the east", the word "hotel" is tagged as "subtopic", which is an
# entity only used with the "grammar" intent)
intent_entity_map = {"grammar": ["subtopic", "function"], "hotel_search": ["area", "price"], \
                     "greet" : [], "affirm" : [], "rest" : [], "goodbye" : [], "reject" : []}

# for each intent, there is a number of template responses, some of which include a placeholder
response_dict = {"greet" : ["Hi, ", "What's up, ", "Hello there! ", "Hey, " ], "goodbye" : ["Goodbye :(", "Hope to see you again soon"],\
                "hotel_search" : ["No such hotel, sorry :(", "{} seems to be a good option", "what about {}?"],\
                 "grammar": ["Unfortunately this is too advanced for me :(", "Here you can find some information: {}", \
                             "Here you can find some examples: {}"], \
                 "rest": ["Can we talk about something else? I'd like to help you on grammar issues", \
                          "What do you mean exactly? Is it something grammar-related", \
                          "We'd better talk about grammar. I don't want to talk about {}-related issues today"], \
				"grammar_check":["You probably meant", "you mean", "All right, i understood", "May be you could have said"], \
                "affirm" : ["Great, hit me up with other questions, grammar related ones of course",\
                            "Good to be on the same page! What else would you like to know?"],\
                "reject" : ["Sorry that I am not helpful. Could you ask me anything else?", \
                            "Maybe other grammar related questions i can relate!"]}

# depending on the selected intent, there will be a selection of database
database_dict = { "grammar" : "grammar_final.db" , "hotel_search" : "hotels.db", \
                 "greet" : None, "goodbye" : None, "rest" : None, }

# in line with the selected intent and database, there will be a base query
query_dict = {"grammar" : "select text FROM grammar_db_v6", "hotel_search" : "select name FROM hotels"}

# lists including different version of asking for a 'description' and 'example', respectively
description_list = ["description", "definition", "define", "what is", "use", "describe", "rules", "form", "to use"]
example_list = ["example", "examples", "exemplify", "sentence with"]

# a dictionary to map all the alternative values of subtopics to a single value that is used in the database
alternatives_dict = {'-ing': 'gerund','-ing form': 'present participle','0 conditional': 'zero conditional',\
 '1 conditional': 'type 1 conditional','2 conditional': 'type 2 conditional','3 conditional': 'type 3 conditional',\
 'a few': 'few','a little': 'little','adding ing': 'gerund','adjective': 'adjective',\
 'adjective comparison': 'adjective comparison','adjective equality': 'adjective equality',\
 'adjective inequality': 'adjective inequality','adjective order': 'order of adjectives',
 'adjective placement': 'placing adjectives','adjectives': 'adjective','adverb': 'adverb',\
 'adverb from adjective': 'adverbs from adjectives','adverbs': 'adverb',\
 'adverbs from adjectives': 'adverbs from adjectives','adverbs of certainty': 'adverbs of certainty',\
 'adverbs of degree': 'adverbs of degree','adverbs of manner': 'adverbs of manner','adverbs of place': 'adverbs of place',\
 'adverbs of time': 'adverbs of time','any': 'some','apostrophe': 'possessive nouns','cardinal': 'numbers',\
 'certainty': 'adverbs of certainty','certainty adverb': 'adverbs of certainty','certainty adverbs': 'adverbs of certainty',\
 'comparative': 'comparative adjectives','comparative adjective': 'comparative adjectives',\
 'comparative adjectives': 'comparative adjectives','comparative adverb': 'comparative adverbs',\
 'comparative adverbs': 'comparative adverbs','comparatives': 'comparative adjectives','comparing adjective': 'adjective comparison',\
 'comparison': 'adjective comparison','comparison of adjectives': 'adjective comparison','compound': 'compound pronouns',\
 'compound pronoun': 'compound pronouns','compound pronouns': 'compound pronouns','conditional 0': 'zero conditional',\
 'conditional 1': 'type 1 conditional','conditional 2': 'type 2 conditional','conditional 3': 'type 3 conditional',\
 'conditional zero': 'zero conditional','contraction': 'contraction','contractions': 'contraction',\
 'countability': 'countable nouns','countable': 'countable nouns','countable noun': 'countable nouns',\
 'countable nouns': 'countable nouns','countables': 'countable nouns','definite': 'definite pronouns',\
 'definite article': 'definite article','definite articles': 'definite article','definite pronoun': 'definite pronouns',\
 'definite pronouns': 'definite pronouns','definite the': 'definite article','definitive pronoun': 'definite pronouns',\
 'degree': 'adverbs of degree','degree adverb': 'adverbs of degree','degree adverbs': 'adverbs of degree',\
 'demonstrative': 'demonstrative','demonstrative determiners': 'demonstrative','demostratives': 'demonstrative',\
 'determiner': 'determiner','determiner another': 'difference words','determiner numbers': 'numbers',\
 'determiner other': 'difference words','determiners': 'determiner','difference word': 'difference words',\
 'difference words': 'difference words','distributive': 'distributive','distributive determiner': 'distributive',\
 'distributive determiners': 'distributive','distributives': 'distributive','equal': 'adjective equality',\
 'equal adjectives': 'adjective equality','equality': 'adjective equality','feminine': 'gendered nouns','few': 'few',\
 'future': 'future simple','future continuous': 'future continuous','future continuous tense': 'future continuous',\
 'future perfect': 'future perfect','future perfect continuous': 'future perfect continuous',\
 'future perfect continuous tense': 'future perfect continuous','future perfect progressive': 'future perfect continuous',\
 'future perfect progressive tense': 'future perfect continuous','future perfect tense': 'future perfect',\
 'future progressive': 'future continuous','future progressive tense': 'future continuous','future simple': 'future simple',\
 'future simple tense': 'future simple','future tense': 'future simple','gender': 'gendered nouns',\
 'gendered nouns': 'gendered nouns','genders': 'gendered nouns','gerund': 'gerund','gerunds': 'gerund',\
 'indefinite': 'indefinite pronouns','indefinite a': 'indefinite article','indefinite an': 'indefinite article',\
 'indefinite article': 'indefinite article','indefinite articles': 'indefinite article','indefinite pronoun': 'indefinite pronouns',\
 'indefinite pronouns': 'indefinite pronouns','indefinitive pronoun': 'indefinite pronouns','inequality': 'adjective inequality',\
 'infinitive': 'infinitive','infinitive form': 'infinitive','infinitive passive': 'passive infinitive',\
 'infinitive with passive': 'passive infinitive','infinitives': 'infinitive','ing form': 'present participle',\
 'interrogative': 'interrogative adverbs','interrogative adverb': 'interrogative adverbs',\
 'interrogative adverbs': 'interrogative adverbs','irregular verb': 'regularity','irregular verbs': 'regularity',\
 'irregularity': 'regularity','little': 'little','manner': 'adverbs of manner','manner adverb': 'adverbs of manner',\
 'manner adverbs': 'adverbs of manner','many': 'many','masculine': 'gendered nouns','mixed conditional': 'mixed conditional',\
 'mixed conditionals': 'mixed conditional','much': 'many','neutral': 'gendered nouns','noun': 'noun','nouns': 'noun',\
 'numbers': 'numbers','object pronoun': 'possessive pronouns','object pronouns': 'possessive pronouns',\
 'order': 'order of adjectives','order of adjective': 'order of adjectives','order of adjectives': 'order of adjectives',\
 'ordinal': 'numbers','ownership': 'possessive nouns','passive': 'passive voice','passive infinitive': 'passive infinitive',\
 'passive tense': 'passive voice','passive voice': 'passive voice','passive with infinitive': 'passive infinitive',\
 'past': 'past simple','past continuous': 'past continuous','past continuous tense': 'past continuous',\
 'past perfect': 'past perfect','past perfect continous tense': 'past perfect continuous',\
 'past perfect continuous': 'past perfect continuous','past perfect progressive': 'past perfect continuous',\
 'past perfect progressive tense': 'past perfect continuous','past perfect tense': 'past perfect',\
 'past progressive': 'past continuous','past progressive tense': 'past continuous','past simple': 'past simple',\
 'past simple tense': 'past simple','past tense': 'past simple','place': 'adverbs of place','place adverb': 'adverbs of place',\
 'place adverbs': 'adverbs of place','placing': 'placing adjectives','placing adjectives': 'placing adjectives',\
 'plural': 'plural nouns','plural noun': 'plural nouns','plural nouns': 'plural nouns','plurality': 'plural nouns',\
 'plurals': 'plural nouns','possessive': 'possessive pronouns','possessive determiner': 'possessive determiner',\
 'possessive determiners': 'possessive determiner','possessive noun': 'possessive nouns','possessive nouns': 'possessive nouns',\
 'possessive pronoun': 'possessive pronouns','possessive pronouns': 'possessive pronouns','possessives': 'possessive pronouns',\
 'pre-determiner': 'pre-determiners','pre-determiners': 'pre-determiners','predeterminer': 'pre-determiners',\
 'predeterminers': 'pre-determiners','present': 'present simple','present continuous': 'present continuous',\
 'present continuous tense': 'present continuous','present participle': 'present participle',\
 'present perfect': 'present perfect','present perfect continuous': 'present perfect continuous',\
 'present perfect continuous tense': 'present perfect continuous','present perfect progressive': 'present perfect continuous',\
 'present perfect progressive tense': 'present perfect continuous','present perfect tense': 'present perfect',\
 'present progressive': 'present continuous','present progressive tense': 'present continuous','present simple': 'present simple',\
 'present simple tense': 'present simple','present tense': 'present simple','preterite': 'past simple','pronoun': 'pronoun',\
 'pronouns': 'pronoun','quantifier': 'quantifier','quantifiers': 'quantifier','regular verb': 'regularity',\
 'regular verbs': 'regularity','regularity': 'regularity','relative adverb': 'relative adverbs','relative adverbs': 'relative adverbs',\
 'relative clause': 'relative clause','relative clauses': 'relative clause','relativity': 'relative adverbs',\
 'sentence formation': 'sentence formation','sentence with relative clause': 'sentence formation',\
 'simple future tense': 'future simple','simple past tense': 'past simple','simple present tense': 'present simple',\
 'singular': 'singular nouns','singular noun': 'singular nouns','singular nouns': 'singular nouns','singulars': 'singular nouns',\
 'some': 'some','subject pronoun': 'possessive pronouns','subject pronouns': 'possessive pronouns',\
 'superlative': 'superlative adjectives','superlative adjective': 'superlative adjectives',\
 'superlative adjectives': 'superlative adjectives','superlative adverb': 'superlative adverbs',\
 'superlative adverbs': 'superlative adverbs','superlatives': 'superlative adjectives','time': 'adverbs of time',\
 'time adverb': 'adverbs of time','time adverbs': 'adverbs of time','type 1 conditional': 'type 1 conditional',\
 'type 1 conditionals': 'type 1 conditional','type 2 conditional': 'type 2 conditional',\
 'type 2 conditionals': 'type 2 conditional','type 3 conditional': 'type 3 conditional',\
 'type 3 conditionals': 'type 3 conditional','type1 conditional': 'type 1 conditional',\
 'type1 conditionals': 'type 1 conditional','type2 conditional': 'type 2 conditional',\
 'type2 conditionals': 'type 2 conditional','type3 conditional': 'type 3 conditional',\
 'type3 conditionals': 'type 3 conditional','uncountability': 'uncountable nouns','uncountable': 'uncountable nouns',\
 'uncountable noun': 'uncountable nouns','uncountable nouns': 'uncountable nouns','uncountables': 'uncountable nouns',\
 'unequal': 'adjective inequality','unequal adjectives': 'adjective inequality','verb': 'verb','verbs': 'verb',\
 'zero conditional': 'zero conditional','zero conditionals': 'zero conditional'}


# initialize global variables for slot filling
params = {}
stored_intent = ""
many = false


# given a grammatically corrected user input message, find it's intent
def intent_classifier(user_message):
    best_intent = interpreter.parse(user_message)
    #print(best_intent["intent"]["confidence"])
    return best_intent["intent"]["name"]


# fill in the dictionary of entity names and corresponding values for a given user message
def find_params(user_message):
    global params
    global many
    print("currently params are", params)
    current_sentence = interpreter.parse(user_message)
    
    # if the number of entities in the given message is zero, that means the user is asking info only on 
    # the intent in general. thus we should empty the global parameters list to avoid unnecessary slot filling
    if len(current_sentence['entities']) == 0:
        params = {}
    # slot filling!!!!!!!!!
    else:
        maintopics = []
        subtopics = []
        for entity in current_sentence['entities']:
            if entity["entity"] in intent_entity_map[current_sentence["intent"]["name"]]: # add entities that only belong to an intent
                if entity["value"] in topic_list:
                    maintopics.append(entity["value"])
                elif entity["value"] in example_list or entity["value"] in description_list:
                    params[entity['entity']] = entity['value']
                else:
                    subtopics.append(entity["value"])
        if len(subtopics) > 1 or len(maintopics) > 1:
            many = True
            for entity in current_sentence["entities"]:
                params[entity['entity']] = entity['value']
        elif len(subtopics) == 1:
            many = False
            for entity in current_sentence["entities"]:
                if entity["value"] not in topic_list:
                    params[entity['entity']] = entity['value']
        else:
            many = False
            for entity in current_sentence["entities"]:
                params[entity['entity']] = entity['value']
                
    return params

def find_query(params, intent):
    database = database_dict[intent]
    query = query_dict[intent] 
    if len(params) > 0:
        filters = ["{}=?".format(k) for k in params]
        query += " WHERE " + " and ".join(filters)
    #print(query)
    # Create the tuple of values
    t = tuple(params.values())
    # Connect to DB
    conn = sqlite3.connect(database)
    # Create a cursor
    c = conn.cursor()
    # Execute the query
    c.execute(query,t)
    # Return the results
    return c.fetchall()

import random
from random import randrange

def generate_response(intent, params):
        
    # start with generic answers to greeting
    if intent == "greet":
        result_candidates = response_dict[intent]
        random_response = random.choice(result_candidates)
        random_question = random.choice(["it's a great day to work on grammar. How can i help you?", \
                                        "i feel really productive today. Shall we start?", \
                                        "how can i help you?"])
        return random_response+random_question, params
        
    
    # hotel_search intent is added
    elif intent == "hotel_search": 
        result_candidates = find_query(params, intent) # given entities and intent, form the query and retrieve data
        if len(result_candidates) > 0:         # there might be multiple results  
            names = [r[0] for r in result_candidates]
            # among all the possible answers, select one randomly
            random_index = randrange(len(names))
            given_name = names[random_index]
            n = min(len(result_candidates),len(response_dict[intent])-1)
            # Select the nth element of the responses array, and format the placeholder with retrieved data if applicable
            return response_dict[intent][n].format(given_name), params
        else:   # if there is no data to show
            return "i'm sorry, i can't find anything", params
        
    # if the intent of the conversation is grammar
    elif intent == "grammar":
        global many
        if many == True:
            return "You've asked about more than one topic at a time. Which one would you like to know more about?", params
        # first, correct entity values to match database
        for entity_value in description_list:
            if entity_value in params.values():
                params["function"] = "description"
        for entity_value in example_list:
            if entity_value in params.values():
                params["function"] = "example"
        if "subtopic" in params.keys():
            if params["subtopic"] in alternatives_dict.keys(): # because sometimes untrained words are assigned to entities
                params["subtopic"] = alternatives_dict[params["subtopic"]]
            else:
                del params["subtopic"]
        
        # then, check whether there are any entities. if not, that means either the user message could
        # not be classified into any subtopic or function group, or the user asked about grammar in general.
        # in either of these cases, direct the user to give more specifications
        if len(params) == 0:
            any_topic = random.choice(list(alternatives_dict.values()))
            message = "Would you like to talk about grammar? If so, could you specify a topic in English grammar, such as \""+ any_topic + "\""
            return message, params
        # also, sometimes the interpreter understands that the user expects an example or a definition, but cannot
        # classify a topic or a subtopic.
        elif ("subtopic" not in params.keys()):
            message = "I see that you need "+params["function"]+ \
            " for something, but i cannot understand what exactly that is. Can you specify the topic again?"
            return message, params
            
        # if there are certain entities involved, then we proceed with generating a response based on the database
        # existence of any entity entails the presence of at most two alternative response candidates in the database
        result_candidates = find_query(params, intent) # given entities and intent, form the query and retrieve data

        # add a minor random element to perk up the responses!
        rand_numb = randrange(1,100)
        if  rand_numb <=25:
            random_ending = " Was that helpful?" 
        elif 26 <= rand_numb <= 50:
            random_ending = " Does that answer your question?" 
        else:
            random_ending = ""
            
        if "function" not in params.keys():
            return response_dict[intent][1].format(result_candidates[0][0])+random_ending, params
        elif "function" in params.keys():
            if params["function"] == "description":
                return response_dict[intent][1].format(result_candidates[0][0])+random_ending, params
            elif params["function"] == "example":
                print(result_candidates)
                return response_dict[intent][2].format(result_candidates[0][0]), params
            else:
                return "there is a problem with 'function' value that is"+params["function"], params

        else: # if there is no data to return, say that you cannot help the user
            return response_dict[intent][0], params
    
    # for any intent that is somehow not in the list of intents 
    elif intent not in intents_list:
        response = random.choice(response_dict["rest"])
        return response.format(intent), params
    
    # for all the other intents that are in the intents list
    else:
        result_candidates = response_dict[intent]
        random_response = random.choice(result_candidates)
        return random_response, params

def respond(user_message):
    intent = intent_classifier(user_message)
    global stored_intent
    global params
    # if there is a change in the intent, empty the params dictionary, and assign the new intent to the stored one
    if stored_intent != intent:
        stored_intent = intent
        params = {}
        params = find_params(user_message)

    # if there is no change in intent, we have to check if the all entities are emptied. If so, the user is talking 
    # only about the intent, but has no interest in any entities.
    else:
        if len(find_params(user_message)) == 0:
            params = {}
        else:
            params = find_params(user_message)	

    response_grammar = res_grammar(user_message, response_dict )
    response_general = generate_response(intent, params)[0].replace("\xa0", " ")
    
    response = response_grammar + response_general
    
        
    return response

# Env Tokens

os.environ['BOTNAME'] = 'bot'
def handle_command(slack_api, command, channel):
	"""
	Recieves commands directed for the bot, if they are valid perform action 
	else resends clarification
	"""
	print( 'Command Text is : ' + command)
	EXAMPLE_COMMAND = 'do'
	
	parsed = interpreter.parse(command)
	response_generated = respond(command.lower())
    
	if len(response_generated) is not 0:
		slack_api.rtm_send_message(channel, response_generated)
	else:
		print ('Invalid Command: Not Understood')
		slack_api.rtm_send_message(channel, 'Invalid Command: Not Understood')

def main():
	"""
	Initiate the bot and call appropriate handler functions
	"""
	READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
	slack_api = slack_utility.connect()
	if slack_api.rtm_connect():
		print ('SLACK_BOT connected and running')
		while True:
			command, channel = slack_utility.parse_slack_response(slack_api.rtm_read())
			if command and channel:
				handle_command(slack_api, command, channel)
			time.sleep(READ_WEBSOCKET_DELAY)
	else:
		print ('Connection failed. Invalid Slack token or bot ID?' )

if __name__ == '__main__':
	main()
