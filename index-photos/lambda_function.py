import json
import urllib.parse
import boto3
import time
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import logging
import datetime
import base64
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

s3 = boto3.client('s3')
rekognition = boto3.client('rekognition')

host = "https:/search-photoscf-x7q7bxq5vlmcwszy5nsdbvd3g4.us-east-1.es.amazonaws.com"
region = "us-east-1"

def lambda_handler(event, context):
    print(event)

    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = urllib.parse.unquote_plus(event["Records"][0]['s3']['object']['key'], encoding='utf-8')
    print(event)
    print(key)
    custom_labels = s3.head_object(Bucket=bucket, Key=key)["Metadata"]["customlabels"]
    print(custom_labels)
    #decode base64
    response = s3.get_object(Bucket=bucket, Key=key)
    content = response['Body'].read().decode("utf-8")
    print("6")
    
    image = base64.b64decode(content)
    
    #delete original photos and upload new one in s3
    response=s3.delete_object(Bucket=bucket,Key=key)
    response=s3.put_object(Bucket=bucket, Body=image, Key=key,ContentType='image/jpg')
    
    # use AWS rekognition to get labels
    labels = get_labels(image)
    
    if custom_labels:
        labels.append(custom_labels)
    
    object_metadata = s3.head_object(Bucket=bucket, Key=key)['Metadata']
    created_timestamp = object_metadata.get('creation-date')
    
    now = datetime.datetime.now()
    created_timestamp = now.strftime("%Y-%m-%dT%H:%M:%S")
    
    json_object = {
        "objectKey": key,
        "bucket": bucket,
        "createdTimestamp": created_timestamp,
        "labels": labels
    }
    
    es_payload=json.dumps(json_object).encode("utf-8")
    
    
    client_OpenSearch = OpenSearch(
        hosts = [{'host': host, 'port':443}],
        http_auth = get_awsauth(region, "es"),
        use_ssl = True,
        verify_certs = True,
        connection_class = RequestsHttpConnection
    )
    
    try:
        response_from_opensearch = client_OpenSearch.index(
        index = 'photos',
        body=es_payload)
        
        print("SUCCESSFULLY")

    except Exception as e:
        logger.error('Failed to upload to ftp: '+ str(e))
        print('Insert Failed OS')
        

def get_labels(image):
    response = rekognition.detect_labels(Image={'Bytes':image}, MaxLabels=10, MinConfidence=90)
    print(response["Labels"])
    labels = [label['Name'] for label in response['Labels']]
    print(labels)
    return labels

def get_awsauth(region, service):
    cred = boto3.Session().get_credentials()
    return AWS4Auth(cred.access_key,
                    cred.secret_key,
                    region,
                    service,
                    session_token=cred.token)
