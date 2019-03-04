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
        # Error count message
        err_num_txt ="error"
        if (error_count>1):
            err_num_txt ="errors"
        err_desc_txt = ""
        for x in range(error_count):
            err_desc_txt = err_desc_txt + " On error no " + str(x+1)+ " at "+  str(matches[x].contextoffset) +" no. char : " +  matches[x].msg + ". "
            
        # error text
        err_text = " You probably have "+ str(error_count) + " " + err_num_txt + " in your sentence."
        response_text = response_text+ err_text + err_desc_txt
    else:
        response_text = ""    
    return response_text