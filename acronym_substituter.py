# -*- coding: utf-8 -*-
"""
Created on Wed Dec  7 00:45:27 2022

@author: m13slash9
"""
# -*- coding: utf-8 -*-
"""
"""
from requests import get
from re import finditer
from random import choice

bracket_types = ["[]","()","<>","\"\"","\'\'","{}","++","\\\\"]

# A function to request the webpage
def get_acronyms(url, term):
    full_url = url + term;
    headers = {'user-agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36'}
    api_resp = get(full_url,headers = headers)
    return api_resp 

# A function to find startpoint and endpoint of a substring in a string
def find_string_parameters(input_string,start_mark,end_mark):
    #start_mark preceeds the required substring
    #end_mark comes after the substring
    input_string = input_string.decode('utf-8')
    #By AkiRoss from stackoverflow
    start_pos = input_string.find(start_mark)
    end_pos = input_string.find(end_mark, start_pos+len(start_mark))
    while start_pos != -1:
        yield (start_pos+len(start_mark) + 1,end_pos)
        start_pos = input_string.find(start_mark, end_pos+1)
        end_pos = input_string.find(end_mark, start_pos+len(start_mark))

# A function that strips html links from all but link text 
def remove_links(input_string):
    input_string = input_string.decode('utf-8')
    if input_string.find('a href=\"http:')!=-1:
        return input_string[(input_string.find(">")+1):input_string.rfind("</")]
    else:
        return input_string

# A function trat removes trailing brackets from the backronym
def remove_brackets(input_string):
    return input_string.split(' (')[0]

# A function that finds a suitable place to insert an acronym into the string
def find_proper_place(input_string, acronym_len):
    #places_for_an_acronym = findall(r"(?=([a-zA-Z]{"+str(acronym_len)+"}))(?![^[]*\])",input_string)
    places_for_an_acronym = finditer("(?=([a-zA-Z]{"+str(acronym_len)+"}))",input_string)
    return places_for_an_acronym

# A function that tests if an acronym is a suitable one
def find_good_acronym(input_acronym,all_meanings):
    #Tests if backronym is good
    good_backronyms = [i for i in all_meanings if ''.join(list(zip(*i.split(' ')))[0]).lower() == input_acronym.lower() and not list(finditer('[^a-zA-Z ]',i))]
    if good_backronyms:
        return good_backronyms[0]
    else:
        return None
    
# A function that requests ancronymfinder and returns a suitable acronym
def give_good_acronym(input_acronym):
    #Because I'd like just one request per acronym
    # Acronymfinder request URL
    acf_url = 'http://www.acronymfinder.com/af-query.asp?p=json&acronym='
    print('Performing web request for \''+input_acronym+'\'')
    request_result = get_acronyms(acf_url, input_acronym);
    all_meanings_generator = find_string_parameters(request_result.content, "result-list__body__meaning\">", "/td")
    all_meanings = [request_result.content[(i[0]+1):(i[1]+1)] for i in all_meanings_generator]
    all_meanings = [remove_brackets(remove_links(i)) for i in all_meanings]
    return find_good_acronym(input_acronym, all_meanings)
    
# A function that finds proper number of substitutions
def several_proper_subs(string_entry, acronym_len, amount_to_find):
    proper_places = [object.span()[0] for object in find_proper_place(string_entry, acronym_len)]
    print("Possible places:",proper_places)
    # Not just list comprehension here because I want to stop iterating after enough matches were found
    if len(proper_places)<amount_to_find:
        print("Impossible!\n")
        return None
    else:
        good_subs = []
        while len(good_subs)<amount_to_find and proper_places:
            if not good_subs:
                good_subs += [(proper_places[0], give_good_acronym(string_entry[proper_places[0]:(proper_places[0]+acronym_len)]),acronym_len)]
            elif proper_places[0]>=good_subs[-1][0]+acronym_len:
                good_subs += [(proper_places[0], give_good_acronym(string_entry[proper_places[0]:(proper_places[0]+acronym_len)]),acronym_len)]
            else:
                pass
            if good_subs and not good_subs[-1][1]:
                good_subs.pop(-1)
            proper_places.pop(0)
    if len(good_subs)==amount_to_find:
        print("Success!\n")
        return good_subs
    else:
        print("Not found enough good acronyms!\n")
        return None

# A function that reduces the abbreviation length and increases the number of places if no substitution is found
def keep_finding_subs(string_entry, requested_length, requested_amount, step_length, step_amount):
    subs_group = None
    while not subs_group and requested_length>0 and requested_amount<len(string_entry):
        print("Searching for "+str(requested_amount)+" acronyms of length "+str(requested_length))
        subs_group = several_proper_subs(string_entry,requested_length,requested_amount)
        requested_length += step_length
        requested_amount += step_amount
    return subs_group

# A function that randomizes a case in the string 
def string_case_randomize(input_string):
    lst = [str.upper, str.lower]
    return ''.join(choice(lst)(c) for c in input_string)

#--------Start of the actual function--------
def acronym_substituter(all_text,string_separator = ' - ',acronym_length = 3, length_step = -1, acronyms_amount = 1, amount_step = 1, randomize_case=True, randomize_brackets=True):

    # For each line the function will remove everything before the separator (leave blank to leave lines intact)
    # acronym_length is the number of letters to substitute with an acronym
    # If found no proper acronyms, the length will be modified by length_step
    # Letters will be substituted with backronyms in acronyms_amount places
    # If found no proper acronyms, the number of places will be modified by amount_step
    # If randomize_case the final result will be case-randomized
    # If randomize_brackets the backronyms will be placed in random brackets, otherwithe in []


    # Split text into lines
    all_entries = all_text.split('\n')

    #Split lines into parts
    if string_separator!='':
        all_entries = [cntr.split(string_separator)[-1] for cntr in all_entries]

    substitution_rules = [keep_finding_subs(i,acronym_length,acronyms_amount,length_step,amount_step) for i in all_entries]

    for i in range(len(all_entries)):
        if substitution_rules[i]:
            for j in reversed(substitution_rules[i]):
                if randomize_brackets:
                    brackets_here = choice(bracket_types)
                else:
                    brackets_here = bracket_types[0]
                all_entries[i] = all_entries[i][:j[0]]+brackets_here[0]+j[1]+brackets_here[1]+all_entries[i][(j[0]+j[2]):]
   
    all_entries = [i+"\n" for i in all_entries];
    if randomize_case:
        return string_case_randomize("".join(all_entries))
    else:
        return "".join(all_entries)
