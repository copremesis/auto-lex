import dialogstate_utils as dialog
import re
import datetime
from prompts_responses import Prompts, Responses

def is_valid(year):
    match = re.search(r'^19|20[0-9]{2}$', year)
    current_year = datetime.datetime.now().year
    
    if match and int(year) <= current_year: 
        return True
    return False
    
def handler(intent_request):
    active_contexts = dialog.get_active_contexts(intent_request)
    session_attributes = dialog.get_session_attributes(intent_request)
    intent = dialog.get_intent(intent_request)
    
    responses = Responses('get_policy_quote')
    prompts = Prompts('get_policy_quote')
    
    # get slots interpreted by lex
    insurance_type = dialog.get_slot('InsuranceType', intent)
    phone_number = dialog.get_slot('PhoneNumber', intent)
    year = dialog.get_slot('VehicleYear', intent)
    zip_code = dialog.get_slot('ZipCode', intent)
    miles_per_year = dialog.get_slot('MilesPerYear', intent)
    
    if year and not miles_per_year:
        if not is_valid(year):
            prompt = prompts.get('re-elicitYear')
            return dialog.elicit_slot(
                active_contexts, session_attributes, intent
                [{'contentType': 'PlainText', 'content': prompt}])
    
    # by default delegate to lex
    return dialog.delegate(active_contexts, session_attributes, intent)