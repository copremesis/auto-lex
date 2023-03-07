"""
 This code sample demonstrates an implementation of the Lex Code Hook Interface
 in order to serve auto insurance bot. Intents, and Slot models which are 
 compatible with this sample can be found in the Lex Console as part of 
 the 'AutoInsurance' template.
"""

import json
import time
import os
import logging
import dialogstate_utils as dialog
import repeat
import add_vehicle
import make_model_year
import make_premium_payment
import electronic_check_payment
import card_payment
import add_driver
import remove_driver
import make_claim
import remove_vehicle
import get_policy_quote
import find_an_advisor
import fallback

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
    
# --- Main handler & Dispatch ---

def dispatch(intent_request):
    """
    Route to the respective intent module code
    """

    intent = dialog.get_intent(intent_request)
    intent_name = intent['name']
    active_contexts = dialog.get_active_contexts(intent_request)
    session_attributes = dialog.get_session_attributes(intent_request)
    
    # Default dialog state is set to delegate
    next_state = dialog.delegate([],{}, intent)
        
    # Dispatch to the respective bot's intent handlers
    if intent_name == "FallbackIntent":
        next_state = fallback.handler(intent_request)
        
    if intent_name == "Repeat":
        next_state = repeat.handler(intent_request)
        
    if intent_name == 'AddVehicle':
        next_state = add_vehicle.handler(intent_request)
        
    if intent_name == 'MakeModelYear':
        next_state = make_model_year.handler(intent_request)
        
    if intent_name == 'MakePremiumPayment':
        next_state = make_premium_payment.handler(intent_request)
        
    if intent_name == 'PaymentByElectronicCheck':
        next_state = electronic_check_payment.handler(intent_request)
        
    if intent_name == 'PaymentByCard':
        next_state = card_payment.handler(intent_request)
        
    if intent_name == 'AddDriver':
        next_state = add_driver.handler(intent_request)
        
    if intent_name == 'RemoveDriver':
        next_state = remove_driver.handler(intent_request)
        
    if intent_name == 'MakeAClaim':
        next_state = make_claim.handler(intent_request)
        
    if intent_name == 'RemoveVehicle':
        next_state = remove_vehicle.handler(intent_request)
        
    if intent_name == 'GetPolicyQuote':
        next_state = get_policy_quote.handler(intent_request)
        
    if intent_name == 'FindAnAdvisor':
        next_state = find_an_advisor.handler(intent_request)
        
    return next_state

def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    # By default, treat the user request as coming from the America/New_York time zone.
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug(event)

    return dispatch(event)
