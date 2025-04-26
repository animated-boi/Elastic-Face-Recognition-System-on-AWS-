import boto3

# Setting up Boto3 EC2 client
ec2 = boto3.resource(
    'ec2',
    region_name='us-east-1',
    aws_access_key_id='KEY VALUE',
    aws_secret_access_key='KEY VALUE'
)

# Using the existing EC2 instance ID
instance_id = "i-09b49dd19da88c366"
instance = ec2.Instance(instance_id)

# Adding tags to the instance
instance.create_tags(
    Tags=[{'Key': 'Name', 'Value': 'WebTier Worker'}]
)
print("Tag 'WebTier Worker' added to the instance.")

# Starting the instance
instance.start()
print("Starting the instance...")

# Wait until the instance is running
instance.wait_until_running()
print(f"Instance {instance_id} is now running.")

