import json
import os
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import time
import logging
import re
import datetime
import requests
import inflection.inflection as inf


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

region = 'us-east-1'
host = 'search-photos-42emiq2wr7v5mrf7fwotrlkx3i.us-east-1.es.amazonaws.com'
index = 'photos'


lexv2 = boto3.client('lexv2-runtime')
def lambda_handler(event, context):
    
    #message from user
    
    msg_from_user = "I want some photos with trees and birds"
    response = lexv2.recognize_text(
            botId='KWBE2WBJUP', # MODIFY HERE
            botAliasId='TSTALIASID', # MODIFY HERE
            localeId='en_US',
            sessionId='testuser',
            text=msg_from_user)
    print("response")
    print(response)
    print("hiiiiii")
    keywords = []
    if 'interpretations' in response and len(response['interpretations']) > 0:
        interpretation = response['interpretations'][0]
        if 'slots' in interpretation["intent"]:
            for key, value in interpretation["intent"]["slots"].items():
                if key in ["Keyword1", "Keyword2"] and value:
                    key_words = value["value"]["interpretedValue"]
                    if " " in key_words:
                        key_words = key_words.split(" ")
                        for word in key_words:
                            keywords.append(inf.singularize(word))
                    else:
                        keywords.append(inf.singularize(key_words))
    
    print(keywords)
    
    if keywords:
        img_paths = search_photos(keywords)
    
    if not img_paths:
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': '*',
            },
            'body': json.dumps({'results': "No Results found"})
        }
    else:    
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': '*',
            },
            'body': json.dumps({'results': img_paths})
        }
                    
                

def search_photos(keywords):
    
    query = {
        "size":3,
        "query": {
            "bool": {
                "should": []
            }
        }
    }

    for key in keywords:
        query['query']['bool']['should'].append({
            "match": {
                "labels": key
            }
        }) 
     
    opensearch = OpenSearch(
        hosts=[{'host': host, 'port': 443}],
        http_auth=get_awsauth(region, "es"),
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )
    
    
    try:
        response = opensearch.search(body = query, index = "photos")
        print(response)
        hits = response['hits']['hits']
        img_list = []
        for element in hits:
            objectKey = element['_source']['objectKey']
            bucket = element['_source']['bucket']
            image_url = "https://" + bucket + ".s3.amazonaws.com/" + objectKey
            img_list.append(image_url)
        return img_list
        
    except Exception as e:
        print(f"Error while searching OpenSearch index: {str(e)}")
        return []
        


def get_awsauth(region, service):
    cred = boto3.Session().get_credentials()
    return AWS4Auth(cred.access_key,
                    cred.secret_key,
                    region,
                    service,
                    session_token=cred.token)

