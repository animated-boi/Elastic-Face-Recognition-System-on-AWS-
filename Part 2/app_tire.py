import boto3
import time
import torch
from facenet_pytorch import InceptionResnetV1
from PIL import Image
import os
import logging

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize the SQS client
sqs = boto3.client('sqs', region_name='us-east-1')

# S3 client
s3 = boto3.client('s3', region_name='us-east-1')

# Define your SQS queues (replace with your actual ASU ID and account info)
request_queue_url = 'https://sqs.us-east-1.amazonaws.com/423623835259/1229421130-req-queue'
response_queue_url = 'https://sqs.us-east-1.amazonaws.com/423623835259/1229421130-resp-queue'

# S3 input and output bucket names
input_bucket_name = '1229421130-in-bucket'
output_bucket_name = '1229421130-out-bucket'

# Initialize your deep learning model
model = InceptionResnetV1(pretrained='vggface2').eval()

def download_image_from_s3(image_key):
    """Download image from S3 input bucket."""
    download_path = f"/tmp/{image_key}"
    try:
        logging.info(f"Downloading {image_key} from S3 bucket {input_bucket_name}.")
        s3.download_file(input_bucket_name, image_key, download_path)
        return download_path
    except Exception as e:
        logging.error(f"Failed to download image from S3: {e}")
        raise

def upload_result_to_s3(filename, result):
    """Upload the classification result to S3 output bucket."""
    try:
        logging.info(f"Uploading result for {filename} to S3 bucket {output_bucket_name}.")
        s3.put_object(Bucket=output_bucket_name, Key=filename, Body=result)
    except Exception as e:
        logging.error(f"Failed to upload result to S3: {e}")
        raise

def process_image(image_path):
    """Process the image and perform model inference."""
    try:
        img = Image.open(image_path)
        img_tensor = torch.tensor(img).unsqueeze(0)  # Convert image to tensor
        logging.info(f"Running inference on {image_path}.")
        with torch.no_grad():
            result = model(img_tensor)
        return result
    except Exception as e:
        logging.error(f"Error processing image: {e}")
        raise

def process_messages():
    """Process messages from the request queue."""
    while True:
        try:
            # Receive message from request queue
            logging.info("Waiting for messages in the request queue...")
            response = sqs.receive_message(
                QueueUrl=request_queue_url,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=10
            )

            if 'Messages' in response:
                for message in response['Messages']:
                    receipt_handle = message['ReceiptHandle']
                    image_key = message['Body']  # This should be the image file name
                    logging.info(f"Received message with image key: {image_key}.")

                    # Download image from S3 input bucket
                    image_path = download_image_from_s3(image_key)

                    # Process image (perform inference)
                    result = process_image(image_path)
                    result_str = str(result)

                    # Upload classification result to S3 output bucket
                    upload_result_to_s3(image_key.split('.')[0], result_str)

                    # Send result to response queue
                    sqs.send_message(
                        QueueUrl=response_queue_url,
                        MessageBody=f"{image_key}:{result_str}"
                    )
                    logging.info(f"Sent result for {image_key} to response queue.")

                    # Delete the processed message from the request queue
                    sqs.delete_message(
                        QueueUrl=request_queue_url,
                        ReceiptHandle=receipt_handle
                    )
                    logging.info(f"Deleted message for {image_key} from request queue.")

                    # Clean up temporary image file
                    os.remove(image_path)
                    logging.info(f"Removed local file {image_path}.")

            else:
                logging.info("No messages in the queue. Waiting...")

            # Add a delay before processing the next message
            time.sleep(5)

        except Exception as e:
            logging.error(f"Error processing messages: {e}")

if __name__ == "__main__":
    logging.info("Starting App Tier...")
    process_messages()
