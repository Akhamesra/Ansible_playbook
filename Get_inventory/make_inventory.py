import boto3
ssm_client = boto3.client('ssm')
ec2_client = boto3.client('ec2')

def get_all_instance_information():
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


response_ec2 = ec2_client.describe_instances(Filters=[{
                        'Name': 'instance-state-name',
                        'Values': ['running']
                    }])

instance_os_type = {'amazon_linux_arm_2' : [],
                  'amazon_linux_arm_below_2' : [],
                  'amazon_linux_amd_2': [],
                  'amazon_linux_amd_below_2' : [],
                  'linux_arm' : [],
                  'linux_amd' : [],
                  'windows' : []}


def get_inventory(all_instance_data,response_ec2):
    os_info = {}
    for instance_info in all_instance_data:
        instance_id = instance_info['InstanceId']
        instance_ip = instance_info['IPAddress']
        os_name = instance_info['PlatformName']
        platversion = instance_info['PlatformVersion']
        os_info[instance_id] = {'instance_ip':instance_ip,
                                'OSName': os_name,
                                'platversion':platversion}

    for reservation in response_ec2['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            architecture = instance['Architecture']
            if instance_id in os_info.keys():
                try:
                    os_info[instance_id]['Architecture']= architecture
                except Exception as e:
                    print(f"##### {instance_id}: instance_id")
            else:
                print(f"##### {instance_id} : instance_id not present in SSM data")

    return os_info

def group_inventory(os_info):
    for info in os_info.values():
        ip = info['instance_ip']
        os_name = info['OSName']
        platversion = info['platversion']
        try:
            arch = 'AMD' if 'x86_64' in info['Architecture'] else 'ARM'
        except Exception as e:
            pass

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

all_instance_data = get_all_instance_information()
os_info = get_inventory(all_instance_data,response_ec2)
group_inventory(os_info)
save_inventory(instance_os_type)