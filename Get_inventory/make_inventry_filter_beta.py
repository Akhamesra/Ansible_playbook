import boto3

def get_ssm_all_instance_information():
    ssm_client = boto3.client('ssm')
    all_instances = []
    next_token = None
    while True:
        if next_token:
            response_ssm = ssm_client.describe_instance_information(NextToken=next_token)
        else:
            response_ssm = ssm_client.describe_instance_information()
        instances = response_ssm.get('InstanceInformationList', [])
        all_instances.extend(instances)
        next_token = response_ssm.get('NextToken', None)
        if not next_token:
            break
    return all_instances

def get_ec2_all_instance_information():
    ec2_client = boto3.client('ec2')
    filters = [
            {
                'Name': 'instance-state-name',
                'Values': ['running']
            },
            {
                'Name': 'tag:LOB',
                'Values': ['Bajajmall', 'BAJAJMALL', 'EMIMALL', 'EMIMALLS']
            }
        ]
    response_ec2 = ec2_client.describe_instances(Filters=filters)
    return response_ec2['Reservations']

def get_inventory(ssm_all_instance_data,ec2_all_instance_data):
    os_info = {}

    for reservation in ec2_all_instance_data:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            architecture = instance['Architecture']
            os_info[instance_id] = {'Architecture':architecture}

    for instance_info in ssm_all_instance_data:
        instance_id = instance_info['InstanceId']
        if instance_id in os_info.keys():
            instance_ip = instance_info['IPAddress']
            os_name = instance_info['PlatformName']
            platversion = instance_info['PlatformVersion']
            os_info[instance_id]['instance_ip']=instance_ip
            os_info[instance_id]['OSName']=os_name
            os_info[instance_id]['platversion']=platversion

    return os_info

def group_inventory(os_info):
    instance_os_type = {'amazon_linux_arm_2' : [],
                  'amazon_linux_arm_below_2' : [],
                  'amazon_linux_amd_2': [],
                  'amazon_linux_amd_below_2' : [],
                  'linux_arm' : [],
                  'linux_amd' : [],
                  'windows' : []}
    
    for info in os_info.values():
        ip = info['instance_ip']
        os_name = info['OSName']
        platversion = info['platversion']
        arch = 'AMD' if 'x86_64' in info['Architecture'] else 'ARM'

        if 'Amazon Linux' in os_name:
            if arch == 'AMD':
                if platversion in ['2023','2']:
                    instance_os_type['amazon_linux_amd_2'].append(ip)
                else:
                    instance_os_type['amazon_linux_amd_below_2'].append(ip)
            else:
                if platversion in ['2023','2']:
                    instance_os_type['amazon_linux_arm_2'].append(ip)
                else:
                    instance_os_type['amazon_linux_arm_below_2'].append(ip)
        elif 'Windows' in os_name:
            instance_os_type['amazon_linux_arm_below_2'].append(ip)

        else:
            if arch == 'AMD':
                instance_os_type['linux_amd'].append(ip)
            else:
                instance_os_type['linux_arm'].append(ip)
    
    return instance_os_type

def save_inventory(instance_os_type):
    count = 0
    with open('inventory.ini', 'w') as f:
        for key, ips in instance_os_type.items():
            f.write(f"[{key}]\n")
            for ip in ips:
                f.write(f"{ip}\n")
            count += len(ips)
            f.write(f"#{len(ips)}")
            f.write("\n")
        f.write(f"#TOTAL IPS : {count}")

ssm_all_instance_data = get_ssm_all_instance_information()
ec2_all_instance_data= get_ec2_all_instance_information()
os_info = get_inventory(ssm_all_instance_data,ec2_all_instance_data)
instance_os_type = group_inventory(os_info)
save_inventory(instance_os_type)
