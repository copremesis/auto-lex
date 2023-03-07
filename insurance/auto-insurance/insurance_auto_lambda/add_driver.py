import dialogstate_utils as dialog
import insurance_system
from datetime import date, timedelta
import json
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
    zip_code = dialog.get_slot('ZipCode', intent)
    first_name = dialog.get_slot('FirstName', intent)
    last_name = dialog.get_slot('LastName', intent)
    driver_dob = dialog.get_slot('DriverDOB', intent)
    marital_status = dialog.get_slot(
        'MaritalStatus', intent, preference = 'interpretedValue')
    relation = dialog.get_slot('Relationship', intent)
    license_number = dialog.get_slot('LicenseNumber', intent)
    license_confirmation = dialog.get_slot('LicenceConfirmation', intent)
    today = date.today()
    
    # Load prompts and responses
    prompts = Prompts('add_driver')
    responses = Responses('add_driver')

    customer_id = dialog.get_session_attribute(intent_request, 'customer_id')
    
    # add slots to session
    if phone_number:
        dialog.set_session_attribute(intent_request, 'phone_number', phone_number)
        session_attributes = dialog.get_session_attributes(intent_request)
        
    if phone_number_confirmation:
        dialog.set_session_attribute(
            intent_request, 'phone_number_confirmation', 
            phone_number_confirmation)
        session_attributes = dialog.get_session_attributes(intent_request)

    phone_number_from_session = dialog.get_session_attribute(
        intent_request, 'phone_number')
    phone_number_confirmation_from_session \
        = dialog.get_session_attribute(
            intent_request, 'phone_number_confirmation')
    
    # get the slots from session        
    if phone_number_from_session: 
        dialog.set_slot('PhoneNumber', phone_number_from_session, intent)
        phone_number = phone_number_from_session
    if phone_number_confirmation_from_session: 
        dialog.set_slot(
            'PhoneNumberConfirmation', phone_number_confirmation_from_session, 
            intent)
        phone_number_confirmation = phone_number_confirmation_from_session
        
    # PhoneNumber confirmation    
    if phone_number and not phone_number_confirmation:
        previous_slot_to_elicit = dialog.get_previous_slot_to_elicit(intent_request)
        if previous_slot_to_elicit == 'PhoneNumberConfirmation':
            if intent['confirmationState'] == 'Confirmed': 
                dialog.set_slot('PhoneNumberConfirmation', 'Confirmed', intent)
                phone_number_confirmation = 'Confirmed'
                prompt = prompts.get('Dob')
                return dialog.elicit_slot(
                            'DOB', active_contexts, session_attributes, intent,
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
                'PhoneNumberConfirmation1', 
                phone_number = phone_number)
                return dialog.confirm_intent(
                    active_contexts,session_attributes, intent,
                    [{'contentType': 'SSML', 'content': prompt}],
                    previous_dialog_action_type='elicit_slot',
                    previous_slot_to_elicit='PhoneNumberConfirmation')
        else:
            prompt = prompts.get(
                'PhoneNumberConfirmation', 
                phone_number = phone_number)
            return dialog.confirm_intent(
                active_contexts,session_attributes, intent,
                [{'contentType': 'SSML', 'content': prompt}],
                previous_dialog_action_type='elicit_slot',
                previous_slot_to_elicit='PhoneNumberConfirmation')
    
    # Get customer id from DB
    if phone_number and dob and not customer_id:
        customer_id, status = insurance_system.get_customer_id(phone_number, dob)
        if not customer_id:
            # flush the slots when customer id is not found
            dialog.set_slot('PhoneNumber', None, intent)
            dialog.set_slot('DOB', None, intent)
            dialog.set_slot('PhoneNumberConfirmation', None, intent)
            dialog.set_session_attribute(intent_request, 'phone_number', None)
            dialog.set_session_attribute(intent_request, "dob", None)
            prompt = prompts.get('re-elicitPhoneNumber2')
            return dialog.elicit_slot(
                'PhoneNumber', active_contexts, session_attributes, intent,
                [{'contentType': 'PlainText', 'content': prompt}])
        else:
            dialog.set_session_attribute(
                                    intent_request, 'customer_id', customer_id)
            prompt = prompts.get('FirstName')
            return dialog.elicit_slot(
                'FirstName',active_contexts, session_attributes,intent,
                [{'contentType': 'PlainText', 'content': prompt}])
    
    if driver_dob and not marital_status:
        previous_slot_to_elicit = dialog.get_previous_slot_to_elicit(
                                                            intent_request)
        print(previous_slot_to_elicit)
        # prompt = prompts.get('MaritalStatus')
        if previous_slot_to_elicit == 'MaritalStatus':
            prompt = prompts.get('re-elicitMaritalStatus')
            return dialog.elicit_slot(
                    'MaritalStatus', active_contexts, session_attributes, intent,
                    [{'contentType': 'PlainText', 'content': prompt}])
        else:
            prompt = prompts.get('MaritalStatus')
            return dialog.elicit_slot(
                    'MaritalStatus', active_contexts, session_attributes, intent,
                    [{'contentType': 'PlainText', 'content': prompt}])
    
    # License confirmation
    if license_number and not license_confirmation:
        previous_slot_to_elicit = dialog.get_previous_slot_to_elicit(
                                                                intent_request)
        if previous_slot_to_elicit == 'LicenceConfirmation':
            if intent['confirmationState'] == 'Confirmed': 
                dialog.set_slot('LicenceConfirmation', 'Confirmed', intent)
                license_confirmation = 'Confirmed'
                prompt = prompts.get('Confirmation', today = today)
                return dialog.confirm_intent(
                    active_contexts, session_attributes, intent,
                    [{'contentType': 'PlainText', 'content': prompt}])
            if intent['confirmationState'] == 'Denied':
                license_confirmation = 'Denied'
                dialog.set_slot('LicenceConfirmation', None, intent)
                prompt = prompts.get('re-elicitLicenseNumber')
                return dialog.elicit_slot(
                    'LicenseNumber', active_contexts, session_attributes, intent,
                    [{'contentType': 'PlainText', 'content': prompt}])
            else:
                prompt = prompts.get(
                'LicenceConfirmation1', license_number = license_number)
                return dialog.confirm_intent(
                    active_contexts, session_attributes, intent,
                    [{'contentType': 'SSML', 'content': prompt}],
                    previous_dialog_action_type='elicit_slot',
                    previous_slot_to_elicit='LicenceConfirmation')
        else:
            prompt = prompts.get(
                'LicenceConfirmation', license_number = license_number)
            return dialog.confirm_intent(
                active_contexts, session_attributes, intent,
                [{'contentType': 'SSML', 'content': prompt}],
                previous_dialog_action_type='elicit_slot',
                previous_slot_to_elicit='LicenceConfirmation')
    
    # Fulfillment
    if license_confirmation and intent['confirmationState'] == 'Confirmed':
        driver_details = {
            "drivers_license_number": license_number,
            "last_name": last_name,
            "first_name": first_name,
            "dob": {"date": dob}
        }   
        status, reason = insurance_system.add_driver(
                                            customer_id, driver_details)
        if status:
            response = responses.get('Fulfilment')
            return dialog.elicit_intent(
                active_contexts, session_attributes, intent,
                [{'contentType': 'PlainText', 'content': response}])
        else:
            prompt = responses.get('Failure')
            return dialog.elicit_intent(
                active_contexts, session_attributes, intent,
                [{'contentType': 'PlainText', 'content': prompt}])
    
    if license_confirmation and intent['confirmationState'] == 'Denied':
        prompt = responses.get('Denied')
        return dialog.elicit_intent(
            active_contexts, session_attributes, intent,
            [{'contentType': 'PlainText', 'content': prompt}])

    # By default delegate to lex
    return dialog.delegate(active_contexts, session_attributes, intent)