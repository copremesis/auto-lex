import boto3
import json
import cfnresponse

client = boto3.client('connect')

def associate_bot(instance_id, bot_alias_arn):
    response2 = client.associate_bot(
        InstanceId=instance_id,
        LexV2Bot={
            'AliasArn': bot_alias_arn
        }
    )

def import_contact_flow(
        instance_id, contact_name, bot_alias_arn, bot_alias_arn2,
        bot_name, bot_name2):
    print('started importing')
    # with open('contact_flow.txt', 'r') as f:
    #     flow = f.read()
    f = open('contact_flow.json',)

    data = json.load(f)
    actions = data.get('Actions')
    action_metadata = data.get('Metadata').get('ActionMetadata')
    for key, value in action_metadata.items():
        if value.get('lexV2BotName') == 'bot_name':
            value['lexV2BotName'] = bot_name
            lex_connection = [d for d in actions if d['Identifier'] == key]
            if lex_connection and len(lex_connection) > 0:
                lex_connection[0]['Parameters']['LexV2Bot']['AliasArn'] = \
                    bot_alias_arn
        if bot_name2 and value.get('lexV2BotName') == 'bot_name2':
            value['lexV2BotName'] = bot_name2
            lex_connection = [d for d in actions if d['Identifier'] == key]
            if lex_connection and len(lex_connection) > 0:
                lex_connection[0]['Parameters']['LexV2Bot']['AliasArn'] = \
                    bot_alias_arn2

    response = client.create_contact_flow (
        InstanceId=instance_id,
        Name=contact_name,
        Type='CONTACT_FLOW',
        Description='Sample flow to connect to Amazon lex bot',
        Content=json.dumps(data)
    )
    if response:
        return 'SUCCESS'
    return 'FAILED'

def parse_arn(arn):
    try:
        elements = arn.split(':', 5)
        result = {
            'arn': elements[0],
            'partition': elements[1],
            'service': elements[2],
            'region': elements[3],
            'account': elements[4],
            'resource': elements[5],
            'resource_type': None
        }
        if '/' in result['resource']:
            result['resource_type'], result['resource'] = result['resource'].split('/',1)
        elif ':' in result['resource']:
            result['resource_type'], result['resource'] = result['resource'].split(':',1)
        return result
    except:
        return {}

# --- Main handler ---
def lambda_handler(event, context):
    try:
        print('event: ', event)
        request_type = event.get('RequestType')
        bot_name = event['ResourceProperties'].get('BotName')
        bot_name2 = event['ResourceProperties'].get('BotName2')
        bot_alias_arn = event['ResourceProperties'].get('BotAliasArn')
        bot_alias_arn2 = event['ResourceProperties'].get('BotAliasArn2')
        instance_arn = event['ResourceProperties'].get('ConnectInstanceARN')
        contact_name = event['ResourceProperties'].get('ContactName')
        response_id = event.get('RequestId')
        instance_id = parse_arn(instance_arn).get('resource')
        if not instance_id:
            response_id = event.get('RequestId')
            reason = "The contact flow is not created. \
                You can continue to work with the chatbot on lexv2 console."
            response = {}
            response['ContactFlowDescription'] = reason
            print(reason)
            cfnresponse.send(
                event, context, cfnresponse.SUCCESS, response, response_id, reason)
            return
        if request_type == 'Create':
            associate_bot(instance_id, bot_alias_arn)
            if bot_alias_arn2:
                associate_bot(instance_id, bot_alias_arn2)
            status = import_contact_flow(
                instance_id, contact_name, bot_alias_arn, bot_alias_arn2,
                bot_name, bot_name2)
            if status == 'SUCCESS':
                response = {}
                response['ContactFlowDescription'] = \
                    "Contact flow "+ contact_name+ " got created succesfully"
                reason = 'Imported contact flow succesfully'
                cfnresponse.send(
                    event, context, cfnresponse.SUCCESS, response,
                    response_id, reason)
            else:
                response = {}
                response['ContactFlowDescription'] = \
                    "Contact flow "+ contact_name+ " creation failed"
                cfnresponse.send(
                    event, context, cfnresponse.SUCCESS, response,
                    response_id, 'Contact import did not go through. \
                        Please import manually')
        elif request_type == 'Delete':
            reason = 'Cannot remove the contact flow. Only the bots are \
                disassociated from the instance'
            response_status = cfnresponse.SUCCESS
            response = {}
            response['ContactFlowDescription'] = reason
            cfnresponse.send(
                event, context, response_status, response, response_id, reason)
    except client.exceptions.DuplicateResourceException as e:
        response_id = event.get('RequestId')
        reason = "Contact flow '"+contact_name+"' already exists. Retry by \
            changing the ContactFlowName parameter when specifying stack details\
            . Exception: "+ str(e)
        cfnresponse.send(
            event, context, cfnresponse.FAILED, {}, response_id, reason)
    except client.exceptions.InvalidRequestException as e:
        response_id = event.get('RequestId')
        reason = "As the instance id: '"+instance_id+"' does not exist, the \
            contact flow is not created. You can continue to work with the \
            chatbot on lexv2 console."
        response = {}
        response['ContactFlowDescription'] = reason
        print(reason)
        cfnresponse.send(
            event, context, cfnresponse.SUCCESS, response, response_id, reason)
    except (client.exceptions.InvalidParameterException,
            client.exceptions.ResourceNotFoundException):
        response_id = event.get('RequestId')
        reason = "The connect parameters are invalid. The contact flow is not \
            created. You can continue to work with the chatbot on lexv2 console."
        response = {}
        response['ContactFlowDescription'] = reason
        print(reason)
        cfnresponse.send(
            event, context, cfnresponse.SUCCESS, response, response_id, reason)
    except Exception as e:
        response_id = event.get('RequestId')
        reason = "Got Exception. Contact flow '"+contact_name+"' cannot be created because of \
            the following exception: "+ str(e)
        print(reason)
        cfnresponse.send(
            event, context, cfnresponse.FAILED, {}, response_id, reason)

