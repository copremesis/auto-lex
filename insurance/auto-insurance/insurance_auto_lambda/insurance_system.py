"""
 Connection to core enterprise system
"""

import boto3
import time
import random
import os
from boto3.dynamodb.conditions import Key, Attr
dynamodb = boto3.resource('dynamodb')

table_name = os.environ['dynamodb_tablename']
insurancedb = dynamodb.Table(table_name)

def get_customer_id(phone_number, given_dob):
    try:
        customers = insurancedb.scan(
            FilterExpression=Attr("record_type").eq('customer') and
            Attr("phone_number").eq(phone_number)
        )
        if len(customers.get('Items')) <= 0 or len(customers.get('Items')) > 1:
            return None, "no record found with matching phone number"
        customer_details = customers.get('Items')[0]
        customer_id = customer_details.get('customer_id')
        customer_dob = customer_details.get('dob')
        
        if given_dob == customer_dob.get('date'):
            return customer_id, "found customer"
        else:
            return None, "date of birth not matching"
    except IndexError:
        return None, "no record found"
    except:
        return None, "unknow error"
        
def make_a_claim(customer_id, incident_details):
    try:
        record_type_id = 'C' + str(round(time.time()))
        claim_record = {
            "customer_id": customer_id,
            "record_type": "claim",
            "record_type_id": record_type_id,
            "incident_details": incident_details
        }
        insurancedb.put_item(Item=claim_record)
        return True, "successful", random.randint(99999,1000000)
    except:
        return False, "unknown issue", -1

def add_vehicle(customer_id, vehicle_details):
    try:
        policies = insurancedb.query(
            KeyConditionExpression=Key('customer_id').eq(customer_id),
            FilterExpression=Attr('record_type').eq('policy')
        )
        if len(policies.get('Items')) <= 0:
            return False, "no record found with matching phone number"
        policyDetails = policies.get('Items')[0]
        policyDetails.get('vehicles').append(vehicle_details)
        insurancedb.put_item(Item=policyDetails)
        return True, "successful"
    except:
        return False, "Unknown issue"

def add_driver(customer_id, driver_details):
    try:
        policies = insurancedb.query(
            KeyConditionExpression=Key('customer_id').eq(customer_id),
            FilterExpression=Attr('record_type').eq('policy'))
        
        if len(policies.get('Items')) <= 0:
            return False, "no record found with matching phone number"
        policyDetails = policies.get('Items')[0]
        policyDetails.get('drivers').append(driver_details)
        insurancedb.put_item(Item=policyDetails)
        return True, "successful added the driver"
    except:
        return False, "failed to add the driver because of an unknow issue"

def match_vehicle(vehicle1, vehicle2):
    if vehicle1.get('vehicle_identification_number'):
        if vehicle1.get('vehicle_identification_number') \
                == vehicle2.get('vehicle_identification_number'):
            return True
    
    valid_vehicle1_details = vehicle1.get('make') and vehicle1.get('model') \
                            and vehicle1.get('year')
    valid_vehicle2_details = vehicle2.get('make') and vehicle2.get('model') \
                            and vehicle2.get('year')
                                                            
    if valid_vehicle1_details and valid_vehicle2_details: 
        if  vehicle1.get('make').lower() == vehicle2.get('make').lower() and \
                vehicle1.get('model').lower() == vehicle2.get('model').lower() and \
                vehicle1.get('year') == vehicle2.get('year'):
            return True
            
    return False
        
def remove_vehicle(customer_id, vehicle_details):
    try:
        policies = insurancedb.query(
            KeyConditionExpression=Key('customer_id').eq(customer_id),
            FilterExpression=Attr('record_type').eq('policy') and
            Attr('policy_type').eq('Vehicle Insurance')
        )
        if len(policies.get('Items')) <= 0:
            return False, "There are no policies for this customer"
        policyDetails = policies.get('Items')[0]
        vehicles = policyDetails.get('vehicles')
        vehicles_count_before = len(vehicles)
        policyDetails['vehicles'] \
            = [x for x in vehicles if not match_vehicle(x, vehicle_details)]
        vehicles_count_after = len(policyDetails['vehicles'])
        if vehicles_count_before == vehicles_count_after:
            return False, "there is no vehicle with the given details"
        insurancedb.put_item(Item=policyDetails)
        return True, "successful in removing the vehicle"
    except IndexError:
        return False, "I couldn't find a match in record"
    except Exception as e:
        return False, "of a system issue. Please try again later"

def check_vehicle_in_policy(customer_id, vehicle_details):
    try:
        policies = insurancedb.query(
            KeyConditionExpression=Key('customer_id').eq(customer_id),
            FilterExpression=Attr('record_type').eq('policy') and
            Attr('policy_type').eq('Vehicle Insurance')
        )
        if len(policies.get('Items')) <= 0:
            return False
        policyDetails = policies.get('Items')[0]
        vehicles = policyDetails.get('vehicles')
        vehicles_count_before = len(vehicles)
        policyDetails['vehicles'] \
            = [x for x in vehicles if not match_vehicle(x, vehicle_details)]
        vehicles_count_after = len(policyDetails['vehicles'])
        if vehicles_count_before == vehicles_count_after:
            return False
        else:
            return True
    except IndexError:
        return False
    except Exception as e:
        return False
        
def match_driver(driver1, driver2):
    if driver1.get('drivers_license_number') \
            and driver2.get('drivers_license_number'):
        if driver1.get('drivers_license_number').lower() \
                == driver2.get('drivers_license_number').lower():
            return True
    if  driver1.get('first_name') == driver2.get('first_name') and \
        driver1.get('last_name') == driver2.get('last_name') and \
        driver1.get('dob')['date'] == driver2.get('dob')['date']:
        return True
    return False
        
def remove_driver(customer_id, driver_details):
    try:
        policies = insurancedb.query(
            KeyConditionExpression=Key('customer_id').eq(customer_id),
            FilterExpression=Attr('record_type').eq('policy') and
            Attr('policy_type').eq('Vehicle Insurance')
        )
        if len(policies.get('Items')) <= 0:
            return False, "There are no policies for this customer"
        policyDetails = policies.get('Items')[0]
        drivers = policyDetails.get('drivers')
        if drivers:
            if not any(
                    d['drivers_license_number'].lower() == \
                    driver_details.get('drivers_license_number').lower() 
                    for d in drivers):
                return False, "there is no driver with the given license number"
        policyDetails['drivers'] \
            = [x for x in drivers if not match_driver(x, driver_details)]
        insurancedb.put_item(Item=policyDetails)
        return True, "removed the driver"
    except IndexError:
        return False, "I couldn't find a match in record"
    except:
        return False, "of a system issue. Please try again later"

def get_next_payment_details(customer_id):
    try:
        policies = insurancedb.query(
            KeyConditionExpression=Key('customer_id').eq(customer_id),
            FilterExpression=Attr('record_type').eq('policy') and
            Attr('policy_type').eq('Vehicle Insurance')
        )
        if len(policies.get('Items')) <= 0:
            return False, None, None, None
        policyDetails = policies.get('Items')[0]
        date = policies['Items'][0]['next_payment']['date']
        remaining_statement_balance \
            = policies['Items'][0]['next_payment']['remaining_statement_balance']
        amount = policies['Items'][0]['next_payment']['amount']
        status = True
        return status, date, remaining_statement_balance, amount
    except:
        return False, None, None, None
        
def get_last_payment_details(customer_id):
    try:
        policies = insurancedb.query(
            KeyConditionExpression=Key('customer_id').eq(customer_id),
            FilterExpression=Attr('record_type').eq('policy') and
            Attr('policy_type').eq('Vehicle Insurance')
        )
        if len(policies.get('Items')) <= 0:
            return None
        policy = policies.get('Items')[0]
        response = {}
        response['last_payment'] = policy.get('last_payment')
        response['zip_code'] = policy['last_payment']['zip']
        response['type_of_payment'] \
            = policy['last_payment']['mode_of_payment']['type']
        response['first_name'] = policy['last_payment']['first_name']
        response['last_name'] = policy['last_payment']['last_name']
        response['card_number'] \
            = policy['last_payment']['mode_of_payment']['card_number']
        response['card_number_last4'] \
            = policy['last_payment']['mode_of_payment']['card_last4_digits']
        return response
    except:
        return None

def make_premium_payment(
        customer_id, mode_of_payment, 
        payment_amount, payment_date, payment_instrument_details):
    try:
        record_type_id = 'P' + str(round(time.time()))
        payment_record = {
            "customer_id": customer_id,
            "record_type": "payment",
            "record_type_id": record_type_id,
            "mode_of_payment": mode_of_payment,
            "payment_amount": payment_amount,
            "payment_status": "pending",
            "payment_date": payment_date,
            "payment_instrument_details": payment_instrument_details
        }
        insurancedb.put_item(Item=payment_record)
        return True, "successful", random.randint(99999,1000000)
    except:
        return False, "failed to process premium payment", -1
    