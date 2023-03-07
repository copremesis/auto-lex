import dialogstate_utils as dialog
import insurance_system
from datetime import date
import json
import random
from prompts_responses import Prompts, Responses

def handler(intent_request):
    active_contexts = dialog.get_active_contexts(intent_request)
    session_attributes = dialog.get_session_attributes(intent_request)
    intent = dialog.get_intent(intent_request)
    
    # get slots interpreted by lex
    phone_number = dialog.get_slot('PhoneNumber', intent)
    phone_number_confirmation = dialog.get_slot(
                                    'PhoneNumberConfirmation', intent)
    dob = dialog.get_slot('DOB', intent)
    make = dialog.get_slot('VehicleMake', intent)
    model = dialog.get_slot('VehicleModel', intent)
    year_of_vehicle = dialog.get_slot('VehicleYear', intent, preference='interpretedValue')
    damage_component = dialog.get_slot('DamageComponent', intent)
    injury_confirmation = dialog.get_slot('InjuryConfirmation', intent)
    incident_location = dialog.get_slot('IncidentLocation', intent)
    vehicle_confirmation = dialog.get_slot('VehicleConfirmation', intent)
    
    # load prompts & responses
    prompts = Prompts('make_claim')
    responses = Responses('make_claim')
    
    customer_id = dialog.get_session_attribute(intent_request, 'customer_id')
    
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
            intent_request, 'phone_number_confirmation')
    
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
                prompt = prompts.get('ReaskPhoneNumber')
                return dialog.elicit_slot(
                            'PhoneNumber',
                            active_contexts, session_attributes, intent,
                            [{'contentType': 'PlainText', 'content': prompt}])
            else:
                prompt = prompts.get('ReaskPhoneNumber1')
                return dialog.elicit_slot(
                    'PhoneNumber',active_contexts,
                    session_attributes,intent,
                    [{'contentType': 'PlainText', 'content': prompt}]) 
        else:
            prompt = prompts.get('PhoneNumberConfirmation', 
                                phone_number = phone_number
                                )
            return dialog.confirm_intent(
                active_contexts, session_attributes, intent,
                [{'contentType': 'SSML', 'content': prompt}],
                previous_dialog_action_type='elicit_slot',
                previous_slot_to_elicit='PhoneNumberConfirmation')
                        
    if phone_number and dob and not customer_id:
        customer_id, status = insurance_system.get_customer_id(phone_number, dob)
        if not customer_id:
            dialog.set_slot('PhoneNumber', None, intent)
            dialog.set_slot('DOB', None, intent)
            dialog.set_slot('PhoneNumberConfirmation', None, intent)
            dialog.set_session_attribute(intent_request, 'phone_number', None)
            dialog.set_session_attribute(intent_request, "dob", None)
            prompt = prompts.get('InvalidPhoneNumber')
            return dialog.elicit_slot(
                'PhoneNumber', active_contexts, session_attributes, intent,
                [{'contentType': 'PlainText', 'content': prompt}])
        else:
            dialog.set_session_attribute(intent_request, 'customer_id', customer_id)
            prompt = prompts.get('Make')
            return dialog.elicit_slot(
                'VehicleMake',active_contexts, session_attributes,intent,
                [{'contentType': 'PlainText', 'content': prompt}]) 
    
    if make and model and year_of_vehicle and not damage_component:
        vehicle_details = {
            "make": make,
            "model": model,
            "year": year_of_vehicle
        }
        status = insurance_system.check_vehicle_in_policy(
            customer_id, vehicle_details)
        previous_slot_to_elicit = dialog.get_previous_slot_to_elicit(
                                                                intent_request)
        if status:
            if previous_slot_to_elicit == 'DamageComponent':
                '''
                 User input did not get resolved to a slot value. So, re-eliciting the 
                 same slot one more time with a guided prompt
                '''
                prompt = prompts.get('re-elicitDamageComponent')
                return dialog.elicit_slot('DamageComponent',active_contexts,
                    session_attributes,intent,
                    [{'contentType': 'PlainText', 'content': prompt}])
        else:
            dialog.set_slot('VehicleMake', None, intent)
            dialog.set_slot('VehicleModel', None, intent)
            dialog.set_slot('VehicleYear', None, intent)
            prompt = prompts.get('Mismatch_re-elicitMake')
            return dialog.elicit_slot(
                'VehicleMake', active_contexts, session_attributes, intent,
                [{'contentType': 'PlainText', 'content': prompt}])
                            
    if damage_component and not incident_location:
        if damage_component == 'Glass':
            response = responses.get('Fulfilment1')
            return dialog.elicit_intent(
                            active_contexts,
                            session_attributes, intent,
                            [{'contentType': 'PlainText', 'content': response}]
                            )
                
    if incident_location and not injury_confirmation:
        prompt = prompts.get('IfInjured')
        return dialog.elicit_slot(
            'InjuryConfirmation',active_contexts,
            session_attributes,intent,
            [{'contentType': 'PlainText', 'content': prompt}])
    
    # fulfilment        
    if injury_confirmation and intent['confirmationState'] == 'Confirmed':
        incident_details = {
            "any_injury":injury_confirmation, 
            "claim_type":damage_component, 
            "make":make, "model":model, 
            "year":year_of_vehicle
        }
        status, reason, confirmation_code \
            = insurance_system.make_a_claim(customer_id, incident_details)
        if status:
            response = responses.get(
                'Fulfilment', confirmation_code = confirmation_code)
            return dialog.elicit_intent(
                active_contexts, session_attributes, intent,
                [{'contentType': 'SSML', 'content': response}])
        else:
            response = responses.get('Failure')
            return dialog.elicit_intent(
                active_contexts, session_attributes, intent,
                [{'contentType': 'PlainText', 'content': response}])
    
    if injury_confirmation and intent['confirmationState'] == 'Denied':
        response = responses.get('Denied')
        return dialog.elicit_intent(
            active_contexts, session_attributes, intent,
            [{'contentType': 'PlainText', 'content': response}])
    
    # confirm intent        
    if injury_confirmation and intent['state'] == 'InProgress':
        prompt = prompts.get('Confirmation')
        return dialog.confirm_intent(
            active_contexts, session_attributes, intent,
            [{'contentType': 'PlainText', 'content': prompt}])
                    
    # by default delegate to lex
    return dialog.delegate(active_contexts, session_attributes, intent)