import dialogstate_utils as dialog
import insurance_system
from datetime import date
import json
from prompts_responses import Prompts, Responses

def handler(intent_request):
    active_contexts = dialog.get_active_contexts(intent_request)
    session_attributes = dialog.get_session_attributes(intent_request)
    intent = dialog.get_intent(intent_request)
    today = date.today()
    
    # get slots interpreted by lex
    phone_number = dialog.get_slot('PhoneNumber', intent)
    phone_number_confirmation = dialog.get_slot(
        'PhoneNumberConfirmation', intent)
    dob = dialog.get_slot('DOB', intent)
    make = dialog.get_slot('VehicleMake', intent)
    model = dialog.get_slot('VehicleModel', intent)
    year_of_vehicle = dialog.get_slot('VehicleYear', intent)
    # vehicle_identification_number = dialog.get_slot(
    #     'vehicle_identification_number', intent)

    customer_id = dialog.get_session_attribute(intent_request, 'customer_id')
    
    # load prompts & responses
    prompts = Prompts('remove_vehicle')
    responses = Responses('remove_vehicle')
    
    if dob:
        dialog.set_session_attribute(intent_request, 'dob', dob)
        session_attributes = dialog.get_session_attributes(intent_request)

    if phone_number:
        dialog.set_session_attribute(intent_request, 'phone_number', phone_number)
        session_attributes = dialog.get_session_attributes(intent_request)
        
    if phone_number_confirmation:
        dialog.set_session_attribute(
            intent_request, 'phone_number_confirmation', 
            phone_number_confirmation)
        session_attributes = dialog.get_session_attributes(intent_request)
        
    phone_number_from_session \
        = dialog.get_session_attribute(
            intent_request, 'phone_number')
    dob_from_session = dialog.get_session_attribute(intent_request, 'dob')
    phone_number_confirmation_from_session \
        = dialog.get_session_attribute(
            intent_request, 'phone_number_confirmation')
    
    # get the slots from session
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
    
    if not customer_id:
        customer_id, status \
            = insurance_system.get_customer_id(phone_number, dob)
        dialog.set_session_attribute(intent_request, 'customer_id', customer_id)
    
    if phone_number and not phone_number_confirmation:
        previous_slot_to_elicit = dialog.get_previous_slot_to_elicit(
                                                                intent_request)
        if previous_slot_to_elicit == 'PhoneNumberConfirmation':
            if intent['confirmationState'] == 'Confirmed': 
                dialog.set_slot('PhoneNumberConfirmation', 'Confirmed', intent)
                phone_number_confirmation = 'Confirmed'
                prompt = prompts.get('AskDob')
                return dialog.elicit_slot(
                    'DOB', active_contexts, session_attributes, intent,
                    [{'contentType': 'PlainText', 'content': prompt}])
            if intent['confirmationState'] == 'Denied':
                dialog.set_slot('PhoneNumberConfirmation', None, intent)
                phone_number_confirmation = 'Denied'
                prompt = prompts.get('re-elicitPhone')
                return dialog.elicit_slot(
                    'PhoneNumber', active_contexts, session_attributes, intent,
                    [{'contentType': 'PlainText', 'content': prompt}])
            else:
                prompt = prompts.get(
                    'PhoneNumberConfirmation1', phone_number = phone_number)
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
        customer_id, status \
            = insurance_system.get_customer_id(phone_number, dob)
        if not customer_id:
            # flush slots and re-elicit when customer id is not found
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
            prompt = prompts.get('AskMake')
            return dialog.elicit_slot(
                'VehicleMake',active_contexts, session_attributes,intent,
                [{'contentType': 'PlainText', 'content': prompt}])
    
    # fulfilment
    if year_of_vehicle and intent['confirmationState'] == 'Confirmed':
        vehicle_details = {
           "model": model,
           "make": make,
           "year": year_of_vehicle
        }
        status, reason \
            = insurance_system.remove_vehicle(customer_id, vehicle_details)
        if status:
            response = responses.get('Fulfilment')
            return dialog.elicit_intent(
                active_contexts, session_attributes, intent,
                [{'contentType': 'PlainText', 'content': response}])
        else:
            response = responses.get('FailureReason', reason=reason)
            return dialog.elicit_intent(
                active_contexts, session_attributes, intent,
                [{'contentType': 'PlainText', 'content': response}]) 
                
    if year_of_vehicle and intent['confirmationState'] == 'Denied':
        response = responses.get('DeniedConfirmation')
        return dialog.elicit_intent(active_contexts, 
                    session_attributes, intent,
                    [{'contentType': 'PlainText', 'content': response}])
    
    # confirm intent                
    if year_of_vehicle and intent['state'] == 'InProgress':
        prompt = prompts.get('Confirmation', today = today)
        return dialog.confirm_intent(
            active_contexts, session_attributes, intent,
            [{'contentType': 'PlainText', 'content': prompt}])
        
    # by default delegate to lex
    return dialog.delegate(active_contexts, session_attributes, intent)
