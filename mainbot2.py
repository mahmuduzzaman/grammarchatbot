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

# Rasa NLU codes
from rasa_nlu.training_data import load_data
training_data = load_data("testData.json") 
from rasa_nlu.config import RasaNLUModelConfig
from rasa_nlu.model import Trainer 
config = RasaNLUModelConfig(configuration_values= {'pipeline': 'spacy_sklearn'}) 
trainer = Trainer(config) 
interpreter = trainer.train(training_data)
# Import sqlite3
import sqlite3

params = {} # later on we have to move this to decide when to empty the parameters dict
def find_params(user_message):
    current_sentence = interpreter.parse(user_message)
    #print(current_sentence['entities'])
    for entity in current_sentence['entities']:
        params[entity['entity']] = entity['value']
    #print("params are", params)
    return params

def find_query(params):
    query = "select name FROM hotels" #this line should be one of the arguments of the function later on
    if len(params) > 0:
        filters = ["{}=?".format(k) for k in params]
        query += " WHERE " + " and ".join(filters)
    # Create the tuple of values
    t = tuple(params.values())
    # Connect to DB
    conn = sqlite3.connect("hotels.db")
    # Create a cursor
    c = conn.cursor()
    # Execute the query
    c.execute(query,t)
    # Return the results
    return c.fetchall()

from random import randrange
responses = ["No such hotel, sorry :(", "{} seems to be a good option", "what about {}?"]
def generate_response(user_message, params):
    candidates = find_query(params)
    if len(candidates[0]) > 0:
        names = [r[0] for r in candidates]
        random_index = randrange(len(names))
        given_name = names[random_index]
        n = min(len(candidates),len(responses)-1)
        # Select the nth element of the responses array
        return responses[n].format(given_name), params
    else:
        return "i'm sorry", params
        


def respond(user_message):
    params = find_params(user_message)
    return generate_response(user_message, params)[0]


# Env Tokens
os.environ['SLACK_TOKEN'] = 'xoxb-528323970259-528632397605-6dZUopuUBG0DAhR3atphsdzM'
os.environ['BOTNAME'] = 'bot'
def handle_command(slack_api, command, channel):
	"""
	Recieves commands directed for the bot, if they are valid perform action 
	else resends clarification
	"""
	print( 'Command Text is : ' + command)
	EXAMPLE_COMMAND = 'do'
	
	parsed = interpreter.parse(command)
	print(parsed)
	
	if command.lower().startswith(EXAMPLE_COMMAND) or command.lower().startswith('what'):

		slack_api.rtm_send_message(channel, 'Yes, code me further to do that!')
	elif command.lower().startswith('hi') or command.lower().startswith('hey') or command.lower().startswith('hello') or command.lower().startswith('who are you'):
		slack_api.rtm_send_message(channel, 'Hey, I\'m your slack bot, how may I help you?')
	elif len(respond(command.lower())) is not 0:
		slack_api.rtm_send_message(channel, respond(command.lower()))
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
