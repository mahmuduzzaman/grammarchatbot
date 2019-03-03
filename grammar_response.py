#!/usr/bin/env python3
import language_check
import random

def res_grammar(text, response_dict):
    response_text= ""
    tool = language_check.LanguageTool('en-US')
    matches = tool.check(text.capitalize())
    error_count = len(matches)
    if (error_count>0):
        corrected_text = language_check.correct(text, matches)
        response_text  = random.choice(response_dict["grammar_check"]) +" - '"+ corrected_text + "'. "
    else:
        response_text = ""    
    return response_text