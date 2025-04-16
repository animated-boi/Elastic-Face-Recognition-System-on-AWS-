import boto3

# Setting up Boto3 EC2 client
ec2 = boto3.resource(
    'ec2',
    region_name='us-east-1',
    aws_access_key_id='AKIAWFIPSXZ53NNWS764',
    aws_secret_access_key='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'
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

