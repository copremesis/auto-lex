import dialogstate_utils as dialog
from datetime import date
import insurance_system
from prompts_responses import Prompts, Responses

def handler(intent_request):
    active_contexts = dialog.get_active_contexts(intent_request)
    session_attributes = dialog.get_session_attributes(intent_request)
    intent = dialog.get_intent(intent_request)
    
    # get slot values from lex
    make = dialog.get_slot('VehicleMake', intent)
    model = dialog.get_slot('VehicleModel', intent)
    year_of_vehicle = dialog.get_slot('VehicleYear', intent)
    type_of_coverage = dialog.get_slot('TypeOfCoverage', intent)
    today = date.today()
    customer_id = dialog.get_session_attribute(intent_request, 'customer_id')
    
    # load prompts & responses
    prompts = Prompts('make_model_year')
    responses = Responses('make_model_year')
      
    # fulfilment                    
    if type_of_coverage and intent['confirmationState'] == 'Confirmed':
        vehicle_details = {
            "make":make, "model":model, 
            "year":year_of_vehicle, 
            "coverage_type":type_of_coverage
        }
        status, statement \
            = insurance_system.add_vehicle(customer_id, vehicle_details)
        if status:
            response = responses.get('Fulfilment')
            return dialog.elicit_intent(
                active_contexts, session_attributes, intent,
                [{'contentType': 'PlainText', 'content': response}])
        else:
            response = responses.get('Failure')
            return dialog.elicit_intent(
                active_contexts, session_attributes, intent,
                [{'contentType': 'PlainText', 'content': response}])
                
    if type_of_coverage and intent['confirmationState'] == 'Denied':
        response = responses.get('Denied')
        return dialog.elicit_intent(
            active_contexts, session_attributes, intent,
            [{'contentType': 'PlainText', 'content': response}])
    
    # confirm intent        
    if type_of_coverage and intent['state'] == 'InProgress':
        prompt = prompts.get('Confirmation', today = today)
        return dialog.confirm_intent(
            active_contexts, session_attributes, intent,
            [{'contentType': 'PlainText', 'content': prompt}])
    
    # by default delegate to lex
    return dialog.delegate(active_contexts, session_attributes, intent)