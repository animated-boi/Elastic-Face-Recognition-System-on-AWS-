import boto3
import time

# Set up the AWS resources
sqs = boto3.client('sqs', region_name='us-east-1')
ec2 = boto3.client('ec2', region_name='us-east-1')

# Queue URLs (get these dynamically after creating the queues)
request_queue_url = f'https://sqs.us-east-1.amazonaws.com/423623835259/1229421130-req-queue'
response_queue_url = f'https://sqs.us-east-1.amazonaws.com/423623835259/1229421130-resp-queue'

# AMI ID of the App Tier (replace with your AMI ID)
app_tier_ami_id = 'ami-06a1cfa97f4d64688'

# Maximum number of app-tier instances
MAX_INSTANCES = 20

# Check queue length and scale accordingly
def autoscale_app_tier():
    while True:
        try:
            # Get the number of messages in the request queue
            print("Checking message count in request queue...")
            response = sqs.get_queue_attributes(
                QueueUrl=request_queue_url,
                AttributeNames=['ApproximateNumberOfMessages']
            )

            message_count = int(response['Attributes']['ApproximateNumberOfMessages'])
            print(f'Debug: Message count in Request Queue: {message_count}')

            # Get the current number of running app-tier instances
            running_instances = get_running_instances()
            running_count = len(running_instances)
            print(f'Debug: Running app-tier instances: {running_count}')

            # Scale out: If there are more messages than running instances, launch more instances
            if message_count > running_count and running_count < MAX_INSTANCES:
                instances_to_launch = min(message_count - running_count, MAX_INSTANCES - running_count)
                print(f'Debug: Launching {instances_to_launch} new instances...')
                launch_instances(instances_to_launch, running_count)

            # Scale in: If there are no messages in the queue, terminate the app-tier instances
            elif message_count == 0 and running_count > 0:
                print('Debug: No messages in the queue. Terminating all instances...')
                terminate_all_instances()

            # Wait before the next check
            print("Waiting for 20 seconds before the next check...")
            time.sleep(20)  # Check every 20 seconds
            
        except Exception as e:
            print(f"Error during autoscaling: {e}")

# Function to get running app-tier instances
def get_running_instances():
    print("Debug: Fetching running app-tier instances...")
    try:
        response = ec2.describe_instances(
            Filters=[{'Name': 'tag:Name', 'Values': ['app-tier-instance-*']},
                     {'Name': 'instance-state-name', 'Values': ['running']}]
        )
        instances = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instances.append(instance['InstanceId'])
        print(f'Debug: Found running instances: {instances}')
        return instances
    except Exception as e:
        print(f"Error fetching running instances: {e}")
        return []

# Function to launch new app-tier instances with sequential names
def launch_instances(count, existing_count):
    print(f'Debug: Preparing to launch {count} new app-tier instances...')
    
    # Create a list of new instance names
    instance_names = [f"app-tier-instance-{i+1}" for i in range(existing_count, existing_count + count)]
    
    for i in range(count):
        instance_name = instance_names[i]
        try:
            print(f'Debug: Launching instance: {instance_name}')
            ec2.run_instances(
                ImageId=app_tier_ami_id,
                MinCount=1,
                MaxCount=1,
                InstanceType='t2.micro',
                KeyName='Project2-Part1-Key-Pair',
                TagSpecifications=[{
                    'ResourceType': 'instance',
                    'Tags': [{'Key': 'Name', 'Value': instance_name}]
                }]
            )
        except Exception as e:
            print(f"Error launching instance {instance_name}: {e}")

# Function to terminate all app-tier instances
def terminate_all_instances():
    print('Debug: Terminating all app-tier instances...')
    running_instances = get_running_instances()
    if running_instances:
        try:
            print(f'Debug: Terminating instances: {running_instances}')
            ec2.terminate_instances(InstanceIds=running_instances)
        except Exception as e:
            print(f"Error terminating instances: {e}")

if __name__ == '__main__':
    autoscale_app_tier()
