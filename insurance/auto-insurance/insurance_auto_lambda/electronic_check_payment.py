import dialogstate_utils as dialog
import insurance_system
from datetime import date
import random
from prompts_responses import Prompts, Responses


def handler(intent_request):
    active_contexts = dialog.get_active_contexts(intent_request)
    session_attributes = dialog.get_session_attributes(intent_request)
    intent = dialog.get_intent(intent_request)
    
    # get slots interpreted by lex
    account_holder_first_name = dialog.get_slot(
        'AccountHolderFirstName' , intent)
    account_holder_last_name = dialog.get_slot('AccountHolderLastName' , intent)
    routing_number = dialog.get_slot(
        'BankRoutingNumber', intent, preference = 'interpretedValue')
    routing_number_confirmation = dialog.get_slot(
        'RoutingNumberConfirmation', intent)
    bank_account_number = dialog.get_slot(
        'BankAccountNumber' , intent, preference = 'interpretedValue')
    bank_account_number_confirmation = dialog.get_slot(
        'AccountNumberConfirmation', intent)
    
    # get slots from the session
    customer_id = dialog.get_session_attribute(intent_request, 'customer_id')
    policy_type = dialog.get_context_attribute(
        active_contexts, 'ElectronicCheckPayment', 'PolicyType')
    mode_of_payment= dialog.get_context_attribute(
        active_contexts, 'ElectronicCheckPayment', 'PaymentMethod')
    payment_amount = dialog.get_context_attribute(
        active_contexts, 'ElectronicCheckPayment', 'PaymentAmount')
    payment_date = dialog.get_context_attribute(
        active_contexts, 'ElectronicCheckPayment', 'Date')
    
    # load prompts & responses
    prompts = Prompts('electronic_check_payment')
    responses = Responses('electronic_check_payment')
    
    if routing_number and not routing_number_confirmation:
        previous_slot_to_elicit = dialog.get_previous_slot_to_elicit(
                                                                intent_request)
        if previous_slot_to_elicit == 'RoutingNumberConfirmation':
            if intent['confirmationState'] == 'Confirmed': 
                dialog.set_slot('RoutingNumberConfirmation', 'Confirmed', intent)
                routing_number_confirmation = 'Yes'
                prompt = prompts.get('BankAccountNumber')
                return dialog.elicit_slot(
                            'BankAccountNumber', active_contexts,
                            session_attributes, intent,
                            [{'contentType': 'PlainText', 'content': prompt}])
            if intent['confirmationState'] == 'Denied':
                dialog.set_slot('RoutingNumberConfirmation', 'Denied', intent)
                routing_number_confirmation = 'No'
                prompt = prompts.get('BankRoutingNumber')
                return dialog.elicit_slot('BankRoutingNumber',active_contexts,
                            session_attributes,
                            intent,
                            [{'contentType': 'PlainText', 'content': prompt}])
            else:
                prompt = prompts.get('BankAccountNumber1')
                return dialog.elicit_slot('BankRoutingNumber',active_contexts,
                            session_attributes,
                            intent,
                            [{'contentType': 'PlainText', 'content': prompt}])
        else:
            prompt = prompts.get(
                                'RoutingConfirmation', 
                                routing_number = routing_number)
            return dialog.confirm_intent(active_contexts,
                            session_attributes, intent,
                            [{'contentType': 'SSML', 'content': prompt}],
                            previous_dialog_action_type='elicit_slot',
                            previous_slot_to_elicit='RoutingNumberConfirmation')
                            
    if bank_account_number and not bank_account_number_confirmation:
        previous_slot_to_elicit = dialog.get_previous_slot_to_elicit(
                                                                intent_request)
        if previous_slot_to_elicit == 'AccountNumberConfirmation':
            if intent['confirmationState'] == 'Confirmed': 
                dialog.set_slot(
                    'AccountNumberConfirmation', 'Confirmed', intent)
                bank_account_number_confirmation = 'Yes'
                return dialog.delegate(
                    active_contexts, session_attributes, intent)
            if intent['confirmationState'] == 'Denied':
                dialog.set_slot('AccountNumberConfirmation', None, intent)
                bank_account_number_confirmation = 'Denied'
                prompt = prompts.get('ReaskBankAccountNumber')
                return dialog.elicit_slot(
                            'BankAccountNumber',active_contexts,
                            session_attributes, intent,
                            [{'contentType': 'PlainText', 'content': prompt}])
            else:
                prompt = prompts.get('ReaskBankAccountNumber1')
                return dialog.elicit_slot(
                            'BankAccountNumber',active_contexts,
                            session_attributes, intent,
                            [{'contentType': 'PlainText', 'content': prompt}])
        else:
            prompt = prompts.get(
                'BankAccountNumberConfirm', 
                bank_account_number=bank_account_number)
            return dialog.confirm_intent(
                active_contexts,session_attributes, intent,
                [{'contentType': 'SSML', 'content': prompt}],
                previous_dialog_action_type='elicit_slot',
                previous_slot_to_elicit='AccountNumberConfirmation')
                
    if bank_account_number_confirmation \
            and intent['confirmationState'] == 'Confirmed':
        status, reason, confirmation_code \
            = insurance_system.make_premium_payment(
                customer_id, mode_of_payment, 
                payment_amount, payment_date, bank_account_number)
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
                
    if bank_account_number_confirmation \
            and intent['confirmationState'] == 'Denied':
        response = prompts.get('Denied')
        return dialog.elicit_intent(
            active_contexts, session_attributes, intent,
            [{'contentType': 'PlainText', 'content': response}])
    
    if bank_account_number_confirmation and intent['state'] == 'InProgress':
        prompt = prompts.get('Confirmation')
        return dialog.confirm_intent(
            active_contexts, session_attributes, intent,
            [{'contentType': 'PlainText', 'content': prompt}])
                            
    # by default delegate to lex
    return dialog.delegate(active_contexts, session_attributes, intent)
    
    
