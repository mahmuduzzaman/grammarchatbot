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
training_data = load_data("grammar_based_data4.json") 
from rasa_nlu.config import RasaNLUModelConfig
from rasa_nlu.model import Trainer 
config = RasaNLUModelConfig(configuration_values= {'pipeline': 'spacy_sklearn'}) 
trainer = Trainer(config) 
interpreter = trainer.train(training_data)

# create dictionaries and lists for later use
intents_list = ["greet", "goodbye", "hotel_search", "grammar", "affirm", "rest", "reject"]
response_dict = {"greet" : ["hi back", "what's up"], "goodbye" : ["goodbye :(", "hope to see you again soon"],\
                "hotel_search" : ["No such hotel, sorry :(", "{} seems to be a good option", "what about {}?"],\
                "grammar": ["unfortunately this is too advanced for me :(", "here you can find some information: {}", \
                             "here you can find some examples: {}"], \
                "rest": ["can we talk about something else? i'd like to help you on grammar issues", \
                          "what do you mean exactly?", \
                          "we'd better talk about grammar. i don't want to talk about {}-related issues today"], \
                "grammar_check":["You probably meant", "you mean", "All right, i understood", "May be you could have said"],
                "affirm" : ["Great, hit me up with other questions", "Good to be on the same page!"],\
                "reject" : ["Sorry that I am not helpful. Could you ask me anything else?", \
                            "Maybe other grammar related questions i can relate!"]}
database_dict = { "grammar" : "grammar_final.db" , "hotel_search" : "hotels.db", "greet" : None, "goodbye" : None, "rest" : None, }
query_dict = {"grammar" : "select text FROM grammar", "hotel_search" : "select name FROM hotels"}

description_list = ["definition", "define", "what is", "use", "describe", "rules", "form", "to use"]
example_list = ["examples", "exemplify", "sentence with"]

# initialize global variables
params = {}
stored_intent = ""



# given a grammatically corrected user input message, find it's intent
def intent_classifier(user_message):
    best_intent = interpreter.parse(user_message)
    #print(best_intent["intent"]["confidence"])
    return best_intent["intent"]["name"]


def find_params(user_message):
    current_sentence = interpreter.parse(user_message)
    for entity in current_sentence['entities']:
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
    if intent == "hotel_search": 
        result_candidates = find_query(params, intent)
        if len(result_candidates) > 0:           
            names = [r[0] for r in result_candidates]
            random_index = randrange(len(names))
            given_name = names[random_index]
            n = min(len(result_candidates),len(response_dict[intent])-1)
            # Select the nth element of the responses array
            return response_dict[intent][n].format(given_name), params
        else:
            return "i'm sorry, i can't find anything", params
    elif intent == "grammar":        
        # correct entity values to match database
        for item in description_list:
            if item in params.values():
                params["function"] = "description"
        for item in example_list:
            if item in params.values():
                params["function"] = "example"

        result_candidates = find_query(params, intent)
        
        # add a minor random element to perk up the responses!
        rand_numb = randrange(1,100)
        if  rand_numb <=25:
            random_ending = " Was that helpful?" 
        elif 26 <= rand_numb <= 50:
            random_ending = " Does that answer your question?" 
        else:
            random_ending = ""
            
        if len(result_candidates) > 0:
            #names = [r[0] for r in result_candidates]
            #print("result cand", result_candidates)
            #print("names" , names)
            #random_index = randrange(len(names))
            #given_name = names[random_index]
            n = min(len(result_candidates),len(response_dict[intent])-1)
            if "description" in params.values(): 
                return response_dict[intent][1].format(result_candidates[0][0])+random_ending, params
            elif "example" in params.values():
                return response_dict[intent][2].format(result_candidates[0][0])+random_ending, params
            else: # in case only the name of the grammar subject but not the function is captured, provide definition
                
                return response_dict[intent][1].format(result_candidates[0][0], result_candidates[1][0])+random_ending, params
        else:
            return response_dict[intent][0], params
    elif intent not in intents_list:
        response = random.choice(response_dict["rest"])
        return response.format(intent), params
    else:
        result_candidates = response_dict[intent]
        random_response = random.choice(result_candidates)
        return random_response, params

def respond(user_message):
    intent = intent_classifier(user_message)
    global stored_intent
    # if there is a change in the intent, empty the params dictionary, and assign the new intent to the stored one
    if stored_intent != intent:
        stored_intent = intent
        global params
        params = {}
    params = find_params(user_message)
    print("params are", params ,  " Intent : " , intent )
    
    response_grammar = res_grammar(user_message, response_dict )
    response_general = generate_response(intent, params)[0]
    
    response = response_grammar + response_general
    
    #print(generate_response(intent, params)[0])
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
