''' To handle MakePremiumPayment intent for the Auto Insurence Bot '''
import dialogstate_utils as dialog
import json
import insurance_system
import logging
from prompts_responses import Prompts, Responses

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def handler(intent_request):
    active_contexts = dialog.get_active_contexts(intent_request)
    session_attributes = dialog.get_session_attributes(intent_request)
    intent = dialog.get_intent(intent_request)
    
    # get slots interpreted by lex
    phone_number = dialog.get_slot('PhoneNumber', intent)
    phone_number_confirmation = dialog.get_slot('PhoneNumberConfirmation', intent)
    dob = dialog.get_slot('DOB', intent)
    policy_type = dialog.get_slot('PolicyType' , intent)
    payment_amount = dialog.get_slot('PaymentAmount' , intent)
    payment_method_confirmation = dialog.get_slot('PaymentMethodConfirmation' , intent)
    payment_method = dialog.get_slot('PaymentMethod' , intent)
    
    customer_id = dialog.get_session_attribute(intent_request, 'customer_id')
    
    # load prompts & responses
    prompts = Prompts('make_premium_payment')
    responses = Responses('make_premium_payment')
    
    if dob:
        dialog.set_session_attribute(intent_request, 'dob', dob)
        session_attributes = dialog.get_session_attributes(intent_request)

    if phone_number:
        dialog.set_session_attribute(
            intent_request, 'phone_number', phone_number)
        session_attributes = dialog.get_session_attributes(intent_request)
        
    if phone_number_confirmation:
        dialog.set_session_attribute(
            intent_request, 'phone_number_confirmation', 
            phone_number_confirmation)
        session_attributes = dialog.get_session_attributes(intent_request)
        
    phone_number_from_session = dialog.get_session_attribute(
        intent_request, 'phone_number')
    dob_from_session = dialog.get_session_attribute(intent_request, 'dob')
    phone_number_confirmation_from_session \
        = dialog.get_session_attribute(
            intent_request, 
            'phone_number_confirmation')
    
    if phone_number_from_session: 
        dialog.set_slot('PhoneNumber', phone_number_from_session, intent)
        phone_number = phone_number_from_session
    if dob_from_session: 
        dialog.set_slot('DOB', dob_from_session, intent)
        dob = dob_from_session
    if phone_number_confirmation_from_session: 
        dialog.set_slot(
            'PhoneNumberConfirmation', 
            phone_number_confirmation_from_session, intent)
        phone_number_confirmation = phone_number_confirmation_from_session
    
    if phone_number and not phone_number_confirmation:
        previous_slot_to_elicit = dialog.get_previous_slot_to_elicit(
                                                                intent_request)
        if previous_slot_to_elicit == 'PhoneNumberConfirmation':
            if intent['confirmationState'] == 'Confirmed': 
                dialog.set_slot('PhoneNumberConfirmation', 'Confirmed', intent)
                phone_number_confirmation = 'Confirmed'
                prompt = prompts.get('Dob')
                return dialog.elicit_slot(
                            'DOB', active_contexts,
                            session_attributes, intent,
                            [{'contentType': 'PlainText', 'content': prompt}])
            if intent['confirmationState'] == 'Denied':
                dialog.set_slot('PhoneNumberConfirmation', None, intent)
                phone_number_confirmation = 'Denied'
                prompt = prompts.get('re-elicitPhoneNumber')
                return dialog.elicit_slot(
                    'PhoneNumber',active_contexts, session_attributes, intent,
                    [{'contentType': 'PlainText', 'content': prompt}])
            else:
                prompt = prompts.get(
                    'PhoneNumberConfirmation', phone_number = phone_number)
                return dialog.confirm_intent(
                    active_contexts, session_attributes, intent,
                    [{'contentType': 'SSML', 'content': prompt}],
                    previous_dialog_action_type='elicit_slot',
                    previous_slot_to_elicit='PhoneNumberConfirmation')
        else:
            prompt = prompts.get(
                'PhoneNumberConfirmation', phone_number = phone_number)
            return dialog.confirm_intent(
                active_contexts, session_attributes, intent,
                [{'contentType': 'SSML', 'content': prompt}],
                previous_dialog_action_type='elicit_slot',
                previous_slot_to_elicit='PhoneNumberConfirmation')
                            
    if phone_number and dob and not customer_id:
        customer_id, status = insurance_system.get_customer_id(phone_number, dob)
        if not customer_id:
            # flush slots
            dialog.set_slot('PhoneNumber', None, intent)
            dialog.set_slot('DOB', None, intent)
            dialog.set_slot('PhoneNumberConfirmation', None, intent)
            dialog.set_session_attribute(intent_request, 'phone_number', None)
            dialog.set_session_attribute(intent_request, "dob", None)
            prompt = prompts.get('InvalidPhone')
            return dialog.elicit_slot(
                'PhoneNumber', active_contexts, session_attributes, intent,
                [{'contentType': 'PlainText', 'content': prompt}])
        else:
            dialog.set_session_attribute(
                intent_request, 'customer_id', customer_id)
    
    if customer_id and not payment_amount:
        status, date, remaining_statement_balance, amount \
            = insurance_system.get_next_payment_details(
                customer_id)
        if status:
            prompt = prompts.get(
                'Amount', 
                remaining_statement_balance = remaining_statement_balance,
                date = date, amount = amount)
            return dialog.elicit_slot(
                'PaymentAmount', active_contexts, session_attributes, intent,
                [{'contentType': 'SSML', 'content': prompt}])  
        else:
            response = responses.get('NoPaymentDue')
            return dialog.elicit_intent(
                active_contexts, session_attributes, intent,
                [{'contentType': 'PlainText', 'content': response}])
                
    if payment_amount:
        status, date, remaining_statement_balance, amount \
            = insurance_system.get_next_payment_details(
                customer_id)
        dialog.set_active_contexts(
            intent_request, 'CardPayment', 
            {
                'PhoneNumber':phone_number, 
                'DOB':dob, 
                'PaymentAmount':payment_amount,
                'PaymentMethod':payment_method,'Date':date
            },
            120, 10)
        dialog.set_active_contexts(
            intent_request, 'ElectronicCheckPayment', 
            {
                'PhoneNumber':phone_number,
                'DOB':dob,
                'PaymentAmount':payment_amount,
                'PaymentMethod':payment_method,'Date':date
            },
            120, 10)
        prompt = prompts.get('PaymentOption')
        return dialog.elicit_intent(
            active_contexts, session_attributes, intent,
            [{'contentType': 'PlainText', 'content': prompt}])
                
    # by default delegate to lex
    return dialog.delegate(active_contexts, session_attributes, intent)
    
    
    