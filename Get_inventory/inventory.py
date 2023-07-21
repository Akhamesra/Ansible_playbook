import boto3
client = boto3.client('ssm')
ec2_client = boto3.client('ec2')

Myec2=ec2_client.describe_instances()

for pythonins in Myec2['Reservations']:
  for printout in pythonins['Instances']:
   print(printout['InstanceId'])

# response_ec2 = ec2_client.describe_instances(Filters=[
#         {
#             'Name': 'instance-id',
#             'Values': [
#                 'i-0ed8e170589de3130'


#             ]
#         },
#     ])
# response = client.describe_instance_information(
#     Filters=[
#         {
#             'Key': 'InstanceIds',
#             'Values': [
#                 'i-0ed8e170589de3130'


#             ]
#         },
#     ],
# )
# for reservation in response_ec2['Reservations']:
#         for instance in reservation['Instances']:
#             instance_id = instance['InstanceId']
#             architecture = instance['Architecture']
#             print(architecture)
            
# details = response['InstanceInformationList']
# # print(details)
# for detail in details:
#     print(detail['IPAddress'], detail['PlatformName'],detail['PlatformType'],detail['PlatformVersion'] )