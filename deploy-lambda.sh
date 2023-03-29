#!/bin/bash

LAMBDA_FUNCTION_NAME="index-photos" # Replace this with your Lambda function name
S3_BUCKET_NAME="bucketp-pipeline" # Replace this with your S3 bucket name
S3_OBJECT_KEY="my-lambda-function-code.zip" # Replace this with the name of the zip file containing your Lambda function code

# Package the Lambda function code into a zip file
zip -r $S3_OBJECT_KEY . -x ".git*" ".*" "*.sh" "*~" -q

# Upload the Lambda function code to S3
aws s3 cp $S3_OBJECT_KEY s3://$S3_BUCKET_NAME/$S3_OBJECT_KEY

# Update the Lambda function code with the latest version
aws lambda update-function-code --function-name $LAMBDA_FUNCTION_NAME --s3-bucket $S3_BUCKET_NAME --s3-key $S3_OBJECT_KEY
- aws lambda update-function-code --function-name $LAMBDA_NAME --region $AWS_DEFAULT_REGION --zip-file fileb://lambda-index-package.zip

# Clean up the zip file
rm $S3_OBJECT_KEY

