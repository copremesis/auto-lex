import dialogstate_utils as dialog
import insurance_system
import datetime
from datetime import date
import random
import re
from prompts_responses import Prompts, Responses

def is_valid_cvv(cvv_number):
    match = re.search(r'^[0-9]{3}$', cvv_number)
    if match: return True
    return False

def handler(intent_request):
    active_contexts = dialog.get_active_contexts(intent_request)
    session_attributes = dialog.get_session_attributes(intent_request)
    intent = dialog.get_intent(intent_request)
    
    # get slots interpreted by lex
    card_number = dialog.get_slot(
        'CardNumber' , intent, preference='interpretedValue')
    card_number_confirmation = dialog.get_slot('CardNumberConfirmation' , intent)
    # card_holder_first_name = dialog.get_slot('CardHolderFirstName' , intent)
    card_holder_last_name = dialog.get_slot('CardHolderLastName' , intent)
    expiry_date = dialog.get_slot('ExpirationDate' , intent)
    cvv_number = dialog.get_slot('CVVNumber' , intent)
    zip_code = dialog.get_slot('Zipcode' , intent)
    prompts = Prompts('card_payment')
    responses = Responses('card_payment')
    
    customer_id = dialog.get_session_attribute(
        intent_request, 'customer_id')
    policy_type = dialog.get_context_attribute(
        active_contexts, 'CardPayment', 'PolicyType')
    mode_of_payment= dialog.get_context_attribute(
        active_contexts, 'CardPayment', 'PaymentMethod')
    payment_amount = dialog.get_context_attribute(
        active_contexts, 'CardPayment', 'PaymentAmount')
    payment_date = dialog.get_context_attribute(
        active_contexts, 'CardPayment', 'Date')
    
    if card_number and not card_number_confirmation:
        previous_slot_to_elicit = dialog.get_previous_slot_to_elicit(
                                                                intent_request)
        if previous_slot_to_elicit == 'CardNumberConfirmation':
            if intent['confirmationState'] == 'Confirmed': 
                dialog.set_slot('CardNumberConfirmation', 'Confirmed', intent)
                card_number_confirmation = 'Confirmed'
                print('confirmed : ', card_number_confirmation)
            elif intent['confirmationState'] == 'Denied':
                dialog.set_slot('CardNumberConfirmation', 'Denied', intent)
                new_card_number_confirmation = 'Denied'
                prompt = prompts.get('re-elicitCardNumber')
                return dialog.elicit_slot(
                    'CardNumber',active_contexts, session_attributes, intent,
                    [{'contentType': 'PlainText', 'content': prompt}])
            else:
                prompt = prompts.get('re-elicitCardNumber1')
                return dialog.elicit_slot(
                    'CardNumber',active_contexts, session_attributes, intent,
                    [{'contentType': 'PlainText', 'content': prompt}])
        else:
            prompt = prompts.get(
                'CardNumberConfirmation', card_number = card_number)
            return dialog.confirm_intent(
                active_contexts, session_attributes, intent,
                [{'contentType': 'SSML', 'content': prompt}],
                previous_dialog_action_type='elicit_slot',
                previous_slot_to_elicit='CardNumberConfirmation')
    
    if expiry_date and not cvv_number:
        expiry_date_strp = datetime.datetime.strptime(expiry_date, "%Y-%m-%d")
        formated_expiry_date = expiry_date_strp.strftime("%B") + ', '\
                                + str(expiry_date_strp.year)
        prompt = prompts.get('CVVNumber', expiry_date=formated_expiry_date)
        print('prompt: ', prompt)
        return dialog.elicit_slot(
            'CVVNumber', active_contexts, session_attributes, intent,
            [{'contentType': 'PlainText', 'content': prompt}])
                
    if cvv_number and intent['confirmationState'] == 'Confirmed':
        status, reason, confirmation_code \
            = insurance_system.make_premium_payment(
                customer_id, mode_of_payment, 
                payment_amount, payment_date, card_number)
        print(status, reason, confirmation_code)
        if status:
            response = responses.get(
                'Fulfilment', confirmation_code = confirmation_code)
            return dialog.elicit_intent(
                active_contexts, session_attributes, intent,
                [{'contentType': 'SSML', 'content': response}])
        else:
            response = prompts.get('Failure')
            return dialog.elicit_intent(
                active_contexts, session_attributes, intent,
                [{'contentType': 'PlainText', 'content': response}])
                
    if cvv_number and intent['confirmationState'] == 'Denied':
        response = prompts.get('Denied')
        return dialog.elicit_intent(
            active_contexts, session_attributes, intent,
            [{'contentType': 'PlainText', 'content': response}])
            
    if cvv_number and intent['state'] == 'InProgress' \
            and intent['confirmationState'] == 'None':
        if not is_valid_cvv(cvv_number):
            prompt= prompts.get('InvalidCVV')
            return dialog.elicit_slot(
            'CVVNumber', active_contexts, session_attributes, intent,
            [{'contentType': 'PlainText', 'content': prompt}])
        else:
            prompt = prompts.get('Confirmation')
            return dialog.confirm_intent(
                active_contexts, session_attributes, intent,
                [{'contentType': 'PlainText', 'content': prompt}])
    
    # by default delegate to lex
    return dialog.delegate(active_contexts, session_attributes, intent)
    
    