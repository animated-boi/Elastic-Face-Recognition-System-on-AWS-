# Defining AWS security credentials
AWS_ACCESS_KEY_ID = "AKIAWFIPSXZ53NNWS764"
AWS_SECRET_ACCESS_KEY = "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"

import boto3

# Setting up Boto3 EC2 client
ec2 = boto3.resource(
    'ec2',
    region_name='us-east-1',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

# Launching an EC2 instance
ami_id = "ami-0866a3c8686eaeeba"  # Ubuntu 24.04 AMI ID
instance = ec2.create_instances(
    ImageId=ami_id,
    MinCount=1,
    MaxCount=1,
    InstanceType="t2.micro",
    KeyName="Project2-Part1-Key-Pair",  # Your key pair name (make sure this matches the key pair you created)
    TagSpecifications=[{
        'ResourceType': 'instance',
        'Tags': [{'Key': 'Name', 'Value': 'WebTier'}]
    }]
)

print("Created EC2 instance with ID:", instance[0].id)

