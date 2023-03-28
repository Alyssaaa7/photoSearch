import json
import urllib.parse
import boto3
import time
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import logging
import datetime

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

s3 = boto3.client('s3')
rekognition = boto3.client('rekognition')

host = "search-photos-42emiq2wr7v5mrf7fwotrlkx3i.us-east-1.es.amazonaws.com"
region = "us-east-1"

def lambda_handler(event, context):
    print(event)

    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = urllib.parse.unquote_plus(event["Records"][0]['s3']['object']['key'], encoding='utf-8')
    
    metadata = s3.head_object(Bucket=bucket, Key=key)['Metadata']
    custom_labels = metadata.get('x-amz-meta-customLabels',[])
    print("This is customLabels", custom_labels)
    
    # use AWS rekognition to get labels
    labels = get_labels(bucket, key)
    
    if custom_labels:
        custom_labels = json.loads(custom_labels)
        labels.extend(custom_labels)
    
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
        

def get_labels(bucket, key):
    response = rekognition.detect_labels(Image={'S3Object':{'Bucket':bucket,'Name':key}}, MaxLabels=10, MinConfidence=90)
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
