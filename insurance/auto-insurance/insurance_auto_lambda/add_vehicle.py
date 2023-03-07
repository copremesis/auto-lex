import dialogstate_utils as dialog
from datetime import date
import re
import make_model_year
import insurance_system
from prompts_responses import Prompts, Responses


def handler(intent_request):
    active_contexts = dialog.get_active_contexts(intent_request)
    session_attributes = dialog.get_session_attributes(intent_request)
    intent = dialog.get_intent(intent_request)
    
    # get slots from lex
    phone_number = dialog.get_slot('PhoneNumber', intent)
    phone_number_confirmation = dialog.get_slot('PhoneNumberConfirmation', intent)
    dob = dialog.get_slot('DOB', intent)
    vin_available = dialog.get_slot('VINAvailable', intent)
    vin = dialog.get_slot('VIN', intent)
    type_of_coverage = dialog.get_slot('TypeofCoverage', intent)
    vehicle_details = {'vehicle_identification_number':vin}
    customer_id = dialog.get_session_attribute(intent_request, 'customer_id')
    today = date.today()
    
    # Load prompts and responses
    prompts = Prompts('add_vehicle')
    responses = Responses('add_vehicle')
    
    # add slots to session
    if dob:
        dialog.set_session_attribute(intent_request, 'dob', dob)
        session_attributes = dialog.get_session_attributes(intent_request)
    if phone_number:
        dialog.set_session_attribute(
            intent_request, 'phone_number', phone_number)
        session_attributes = dialog.get_session_attributes(intent_request)
    if phone_number_confirmation:
        dialog.set_session_attribute(
            intent_request, 'phone_number_confirmation', phone_number_confirmation)
        session_attributes = dialog.get_session_attributes(intent_request)
        
    phone_number_from_session = dialog.get_session_attribute(
        intent_request, 'phone_number')
    dob_from_session = dialog.get_session_attribute(intent_request, 'dob')
    phone_number_confirmation_from_session \
        = dialog.get_session_attribute(intent_request, 'phone_number_confirmation')
    
    # get slots from session
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
    
    # PhoneNumber confirmation
    if phone_number and not phone_number_confirmation:
        previous_slot_to_elicit = dialog.get_previous_slot_to_elicit(
                                                                intent_request)
        if previous_slot_to_elicit == 'PhoneNumberConfirmation':
            if intent['confirmationState'] == 'Confirmed': 
                dialog.set_slot('PhoneNumberConfirmation', 'Confirmed', intent)
                phone_number_confirmation = 'Confirmed'
                prompt = prompts.get('Dob')
                return dialog.elicit_slot(
                    'DOB', active_contexts, session_attributes, intent,
                    [{'contentType': 'PlainText', 'content': prompt}])
            if intent['confirmationState'] == 'Denied':
                dialog.set_slot('PhoneNumberConfirmation', 'Denied', intent)
                phone_number_confirmation = 'Denied'
                prompt = prompts.get('PhoneNumber')
                return dialog.elicit_slot(
                    'PhoneNumber', active_contexts, session_attributes, intent,
                    [{'contentType': 'PlainText', 'content': prompt}])
            else:
                prompt = prompts.get(
                'PhoneNumberConfirmation1', phone_number=phone_number)
                return dialog.confirm_intent(
                    active_contexts,session_attributes, intent,
                    [{'contentType': 'SSML', 'content': prompt}],
                    previous_dialog_action_type='elicit_slot',
                    previous_slot_to_elicit='PhoneNumberConfirmation')
        else:
            prompt = prompts.get(
                'PhoneNumberConfirmation', phone_number = phone_number)
            return dialog.confirm_intent(
                active_contexts,session_attributes, intent,
                [{'contentType': 'SSML', 'content': prompt}],
                previous_dialog_action_type='elicit_slot',
                previous_slot_to_elicit='PhoneNumberConfirmation')
    
    # get the customer id from DB            
    if phone_number and dob and not customer_id:
        customer_id, status = insurance_system.get_customer_id(phone_number, dob)
        if not customer_id:
            # Flush the slots & re-elicit from the start
            dialog.set_slot('PhoneNumber', None, intent)
            dialog.set_slot('DOB', None, intent)
            dialog.set_slot('PhoneNumberConfirmation', None, intent)
            dialog.set_session_attribute(intent_request, 'phone_number', None)
            dialog.set_session_attribute(intent_request, "dob", None)
            prompt = prompts.get('re-elicitPhoneNumber')
            return dialog.elicit_slot(
                'PhoneNumber', active_contexts, session_attributes, intent,
                [{'contentType': 'PlainText', 'content': prompt}])
        else:
            dialog.set_session_attribute(
                intent_request, 'customer_id', customer_id)
            prompt = prompts.get('VINAvailable')
            return dialog.confirm_intent(
                active_contexts, session_attributes, intent,
                [{'contentType': 'PlainText', 'content': prompt}],
                previous_dialog_action_type='elicit_slot',
                previous_slot_to_elicit='VINAvailable')
    
    if customer_id and not vin_available:
        previous_slot_to_elicit = dialog.get_previous_slot_to_elicit(
                                                                intent_request)
        if previous_slot_to_elicit == 'VINAvailable':
            if intent['confirmationState'] == 'Confirmed': 
                dialog.set_slot('VINAvailable', 'Confirmed', intent)
                vin = 'Confirmed'
                prompt = prompts.get('Vin')
                return dialog.elicit_slot(
                    'VIN', active_contexts, session_attributes, intent,
                    [{'contentType': 'PlainText', 'content': prompt}])
            if intent['confirmationState'] == 'Denied':
                dialog.set_slot('VINAvailable', 'Denied', intent)
                vin_available = 'Denied'
                prompt = prompts.get('MakeModelYear')
                dialog.set_active_contexts(
                    intent_request, 'AddVehicle', {}, 120, 10)
                return dialog.elicit_intent(
                    active_contexts, session_attributes, intent,
                    [{'contentType': 'PlainText', 'content': prompt}])
            else:
                prompt = prompts.get('re-elicitVin')
                return dialog.elicit_slot(
                    'VINAvailable',active_contexts, session_attributes,
                    intent, [{'contentType': 'PlainText', 'content': prompt}]) 
        else:
            prompt = prompts.get('VINAvailable')
            return dialog.confirm_intent(
                active_contexts, session_attributes, intent,
                [{'contentType': 'PlainText', 'content': prompt}],
                previous_dialog_action_type='elicit_slot',
                previous_slot_to_elicit='VINAvailable')
                
    if vin_available and not vin:
        prompt = prompts.get('Vin')
        return dialog.elicit_slot(
            "VIN", active_contexts, session_attributes, intent,
            [{'contentType': 'PlainText', 'content': prompt}])
    
    if vin and not type_of_coverage:
        prompt = prompts.get('TypeofCoverage')
        return dialog.elicit_slot(
            'TypeofCoverage', active_contexts, session_attributes, intent,
            [{'contentType': 'PlainText', 'content': prompt}])
    
    # confirm intent    
    if type_of_coverage and intent['state'] == 'InProgress' \
            and intent['confirmationState'] == 'None':
        prompt = prompts.get('Confirmation', today = today)
        return dialog.confirm_intent(
            active_contexts, session_attributes, intent,
            [{'contentType': 'PlainText', 'content': prompt}])

    # fulfillment
    if type_of_coverage and intent['confirmationState'] == 'Confirmed':
        status, statement = insurance_system.add_vehicle(
                                                customer_id, vehicle_details)
        if status:
            response = responses.get('Fulfilment')
            return dialog.elicit_intent(
                active_contexts, session_attributes, intent,
                [{'contentType': 'PlainText', 'content': response}])
        else:
            response = prompts.get('Failure')
            return dialog.elicit_intent(
                active_contexts, session_attributes, intent,
                [{'contentType': 'PlainText', 'content': response}])
    
    if type_of_coverage and intent['confirmationState'] == 'Denied':
        response = responses.get('Denied')
        return dialog.elicit_intent(
            active_contexts, session_attributes, intent,
            [{'contentType': 'PlainText', 'content': response}])
    
    # by default delegate to lex
    return dialog.delegate(active_contexts, session_attributes, intent)

    