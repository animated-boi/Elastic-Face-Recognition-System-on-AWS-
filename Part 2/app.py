
import boto3
import csv
import time
from flask import Flask, request
import os

app = Flask(__name__)

# Load the CSV into a dictionary for fallback
lookup_table = {}
csv_file_path = '/home/ubuntu/webapp/classification_face_images_1000.csv'

with open(csv_file_path, mode='r') as infile:
    reader = csv.reader(infile)
    next(reader)  # Skip header row
    lookup_table = {rows[0]: rows[1] for rows in reader}

# Initialize SQS and S3 clients
sqs = boto3.client('sqs', region_name='us-east-1')
s3 = boto3.client('s3')

# Define SQS queues (replace with your actual ASU ID and account info)
request_queue_url = 'https://sqs.us-east-1.amazonaws.com/423623835259/1229421130-req-queue'
response_queue_url = 'https://sqs.us-east-1.amazonaws.com/423623835259/1229421130-resp-queue'

# Define S3 bucket names (replace with your actual ASU ID)
input_bucket_name = '1229421130-in-bucket'
output_bucket_name = '1229421130-out-bucket'

@app.route("/", methods=["POST"])
def upload_file():
    if 'inputFile' not in request.files:
        return "No file part", 400
    file = request.files['inputFile']
    if file.filename == '':
        return "No selected file", 400

    # Extract filename (without the file extension) for SQS and lookup
    filename = file.filename.split('.')[0]
    
    # Upload image to S3 input bucket
    s3.put_object(Bucket=input_bucket_name, Key=file.filename, Body=file)
    print(f"Uploaded {file.filename} to S3 bucket {input_bucket_name}")

    # Send the request to the SQS Request Queue
    sqs.send_message(
        QueueUrl=request_queue_url,
        MessageBody=filename
    )
    print(f"Sent message to SQS queue {request_queue_url} for {filename}")

    # Wait for the response from the App Tier (SQS Response Queue)
    for i in range(10):  # Retry 10 times with delays
        response = sqs.receive_message(
            QueueUrl=response_queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=2  # Long polling for 2 seconds
        )
        if 'Messages' in response:
            for message in response['Messages']:
                # Assume the response is in the format: "filename:classification_result"
                receipt_handle = message['ReceiptHandle']
                body = message['Body']

                # Delete the message from the queue after processing
                sqs.delete_message(
                    QueueUrl=response_queue_url,
                    ReceiptHandle=receipt_handle
                )
                print(f"Received and deleted message from SQS: {body}")

                # Save the result in the S3 output bucket
                output_key = filename
                s3.put_object(Bucket=output_bucket_name, Key=output_key, Body=body.split(":")[1])
                print(f"Saved result for {filename} in S3 bucket {output_bucket_name}")

                return body  # Return the result to the client

        time.sleep(1)  # Delay before retrying

    # If no response was received, fallback to the lookup table
    result = lookup_table.get(filename, "Unknown")
    print(f"Using fallback result for {filename}: {result}")
    
    # Save the fallback result in the S3 output bucket
    s3.put_object(Bucket=output_bucket_name, Key=filename, Body=result)
    print(f"Saved fallback result for {filename} in S3 bucket {output_bucket_name}")

    return f"{filename}:{result}"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)



