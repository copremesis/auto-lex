import dialogstate_utils as dialog
from prompts_responses import Responses

def handler(intent_request):
    active_contexts = dialog.get_active_contexts(intent_request)
    session_attributes = dialog.get_session_attributes(intent_request)
    intent = dialog.get_intent(intent_request)
    responses = Responses('find_an_advisor')
    
    # fulfilment
    response = responses.get('fulfilment')
    return dialog.elicit_intent(
        active_contexts, session_attributes, intent,
        [{'contentType': 'PlainText', 'content': response}])