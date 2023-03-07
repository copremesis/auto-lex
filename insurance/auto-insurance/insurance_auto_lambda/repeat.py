import dialogstate_utils as dialog
import json

def handler(intent_request):
    active_contexts = dialog.get_active_contexts(intent_request)
    session_attributes = dialog.get_session_attributes(intent_request)
    intent = dialog.get_intent(intent_request)
    previous_message = dialog.get_session_attribute(intent_request, 'previous_message')
    
    if previous_message:
        return dialog.elicit_intent(active_contexts, session_attributes, intent, json.loads(previous_message))
    else:
        return dialog.elicit_intent(
            active_contexts, session_attributes, intent, 
            [{
                'contentType': 'PlainText', 
                'content': "I am sorry. I am unable to repeat that. \
                    Is there anything else I can help you with?"}])
    