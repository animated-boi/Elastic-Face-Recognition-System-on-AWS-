import boto3
import time

# Set your ASU ID
ASU_ID = '12'  # Replace with your actual ASU ID

# Set up the AWS resources
sqs = boto3.client('sqs', region_name='us-east-1')
ec2 = boto3.client('ec2', region_name='us-east-1')

# Queue URLs (get these dynamically after creating the queues)
request_queue_url = f'https://sqs.us-east-1.amazonaws.com/423623835259/1229421130-req-queue'
response_queue_url = f'https://sqs.us-east-1.amazonaws.com/423623835259/1229421130-resp-queue'

# AMI ID of the App Tier (replace with your AMI ID)
app_tier_ami_id = 'ami-084e1e7cd0609a59b'

# Maximum number of app-tier instances
MAX_INSTANCES = 20

# Check queue length and scale accordingly
def autoscale_app_tier():
    while True:
        # Get the number of messages in the request queue
        response = sqs.get_queue_attributes(
            QueueUrl=request_queue_url,
            AttributeNames=['ApproximateNumberOfMessages']
        )
        
        message_count = int(response['Attributes']['ApproximateNumberOfMessages'])
        print(f'Message count in Request Queue: {message_count}')

        # Get the current number of running app-tier instances
        running_instances = get_running_instances()
        running_count = len(running_instances)
        print(f'Running app-tier instances: {running_count}')
        
        # Scale out: If there are more messages than running instances, launch more instances
        if message_count > running_count and running_count < MAX_INSTANCES:
            instances_to_launch = min(message_count - running_count, MAX_INSTANCES - running_count)
            launch_instances(instances_to_launch, running_count)
        
        # Scale in: If there are no messages in the queue, terminate the app-tier instances
        elif message_count == 0 and running_count > 0:
            terminate_all_instances()

        # Wait before the next check
        time.sleep(20)  # Check every 30 seconds


# Function to get running app-tier instances
def get_running_instances():
    response = ec2.describe_instances(
        Filters=[{'Name': 'tag:Name', 'Values': ['app-tier-instance-*']},
                 {'Name': 'instance-state-name', 'Values': ['running']}]
    )
    
    instances = []
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instances.append(instance['InstanceId'])
    return instances

# Function to launch new app-tier instances with sequential names
def launch_instances(count, existing_count):
    print(f'Launching {count} app-tier instances...')
    
    # Create a list of new instance names
    instance_names = [f"app-tier-instance-{i+1}" for i in range(existing_count, existing_count + count)]
    
    for i in range(count):
        instance_name = instance_names[i]
        print(f'Launching instance: {instance_name}')
        
        ec2.run_instances(
            ImageId=app_tier_ami_id,
            MinCount=1,
            MaxCount=1,
            InstanceType='t2.micro',
            KeyName='Project2-Part1-Key-Pair'
            TagSpecifications=[{
                'ResourceType': 'instance',
                'Tags': [{'Key': 'Name', 'Value': instance_name}]
            }]
        )

# Function to terminate all app-tier instances
def terminate_all_instances():
    print('Terminating all app-tier instances...')
    running_instances = get_running_instances()
    if running_instances:
        ec2.terminate_instances(InstanceIds=running_instances)

if __name__ == '__main__':
    autoscale_app_tier()

