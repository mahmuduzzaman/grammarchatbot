#!/usr/bin/env python3
import language_check
import random
import inflect

def res_grammar(text, response_dict):
    
    rest_text = text[1:]
    text      = text[0].capitalize() + rest_text
    p = inflect.engine()
    
    response_text= ""
    tool = language_check.LanguageTool('en-US')
    matches = tool.check(text)
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
            start = matches[x].contextoffset
            end   = matches[x].contextoffset+matches[x].errorlength
            err_desc_txt = err_desc_txt + " " + p.ordinal(x+1)+ " error is in '"+ text[start:end]  +"' : " +  matches[x].msg + ". "
            
        # error text
        err_text = " You probably have "+ str(error_count) + " " + err_num_txt + " in your sentence."
        response_text = response_text+ err_text + err_desc_txt
    else:
        response_text = ""    
    return response_text