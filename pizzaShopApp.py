from __future__ import print_function
from boto3.dynamodb.conditions import Key, Attr
import boto3
import json
import datetime
# Get the service resource.
dynamodb = boto3.resource('dynamodb')
print('Loading function')

def lambda_handler(event, context):
    table_order = dynamodb.Table('order')
    table_menu = dynamodb.Table('pizzaStore')
    operations = {
        'DELETE': lambda dynamo, x: dynamo.delete_item(**x),
        'GET': lambda dynamo, x: dynamo.scan(**x),
        'POST': lambda dynamo, x: dynamo.put_item(**x),
        'PUT': lambda dynamo, x: dynamo.update_item(**x),
    }
    operation = event['method']
    if operation in operations:
        if operation == 'POST':
            name = event['body']['customer_name']
            menu_id = event['body']['menu_id']
            order_id = event['body']['order_id']
            table_order.put_item(Item=event['body'])
            response = table_menu.query(
                ProjectionExpression="selection",
                KeyConditionExpression=Key('menu_id').eq(menu_id)
                )
            selection = response['Items'][0]['selection']
            output = "Hi "+name+" please choose one of these selection:"
            i=1
            for items in selection:
                output+=" "+str(i)+". "+items
                i=i+1
            res={'Message' : output}
            table_order.update_item(
                Key={
                    'order_id': order_id,
                     },
                UpdateExpression='SET order_status = :val1',
                ExpressionAttributeValues={
                    ':val1': "selection"
                     })
            return(res)
        if operation == 'PUT':
            order_id = event['params']['order_id']
            sel_input = event['body']['input']
            
            order_res = table_order.query(
                ProjectionExpression="menu_id,order_status",
                KeyConditionExpression=Key('order_id').eq(order_id)
                )
            menu_id = order_res['Items'][0]['menu_id']
            order_status = order_res['Items'][0]['order_status']
            response = table_menu.query(
                ProjectionExpression="selection,size,price",
                KeyConditionExpression=Key('menu_id').eq(menu_id)
                )
            if (order_status == "selection"):
                selection = response['Items'][0]['selection'][int(sel_input)-1]
                order= {order_status: selection}
                size = response['Items'][0]['size']
                output = "Which size do you want?"
                i=1
                for items in size:
                    output+=" "+str(i)+". "+items
                    i=i+1
                res={'Message' : output}
                table_order.update_item(
                Key={
                    'order_id': order_id,
                     },
                UpdateExpression='SET order_status = :val1, #O = :val2',
                ExpressionAttributeNames={
                    '#O': "order"
                     },
                ExpressionAttributeValues={
                    ':val1': "size",
                    ':val2': order
                     })
                return(res)
            if (order_status == "size"):
                size = response['Items'][0]['size'][int(sel_input)-1]
                costs = response['Items'][0]['price'][int(sel_input)-1]
                now = datetime.datetime.now()
                order_time = now.strftime("%m-%d-%Y@%H:%M:%S")
                response = table_order.query(
                ProjectionExpression="#O",
                ExpressionAttributeNames={
                    '#O': "order"
                     },
                KeyConditionExpression=Key('order_id').eq(order_id)                                                                                                                                                                                                                         
                )
                selection = response['Items'][0]['order']['selection']
                order={'selection': selection,order_status: size,'costs':costs,'order_time':order_time}
                output = "Your order costs $"+costs+". We will email you when the order is ready. Thank you!"
                res={'Message' : output}
                table_order.update_item(
                Key={
                    'order_id': order_id,
                     },
                UpdateExpression='SET order_status = :val1, #O = :val2',
                ExpressionAttributeNames={
                    '#O': "order"
                     },
                ExpressionAttributeValues={
                    ':val1': "processing",
                    ':val2': order
                     })
                return(res)
        if operation == 'GET':
            order_id = event['params']['order_id']
            response = table_order.query(
                ProjectionExpression="menu_id,order_id,customer_name,customer_email,order_status,#O",
                ExpressionAttributeNames={
                    '#O': "order"
                     },
                KeyConditionExpression=Key('order_id').eq(order_id)
                )
            return(response['Items'][0])
            
    else:
        return respond(ValueError('Unsupported method "{}"'.format(operation)))

