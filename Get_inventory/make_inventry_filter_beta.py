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
            try:
                instance_id = instance['InstanceId']
                architecture = instance['Architecture']
                tags = instance['Tags']
                name = ""
                lob = ""
                for tag in tags:
                    if tag['Key'] == 'Name':
                        name= tag['Value']
                    elif tag['Key'] == 'LOB':
                        lob= tag['Value']
                os_info[instance_id] = {'Architecture':architecture,
                                        'Name':name,
                                        'LOB':lob}
            except Exception as e:
                print(f"ERROR in ec2.client for instance - {instance} - {e} ")

    for instance_info in ssm_all_instance_data:
        instance_id = instance_info['InstanceId']
        if instance_id in os_info.keys():
            try:
                instance_ip = instance_info['IPAddress']
                try:
                    os_name = instance_info['PlatformName']
                except:
                    os_name = instance_info['PlatformType']
                try:
                    platversion = instance_info['PlatformVersion']
                except:
                    platversion = "NOT_FOUND"
                os_info[instance_id]['instance_ip']=instance_ip
                os_info[instance_id]['OSName']=os_name
                os_info[instance_id]['platversion']=platversion
            except Exception as e:
                print(f"ERROR in ssm.client for instance - {instance} - {e} ")

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
        name = ""
        lob = ""
        try:
            arch = 'AMD' if 'x86_64' in info['Architecture'] else 'ARM'
            try:
                ip = info['instance_ip']
            except:
                print("Excluding")
                continue
            os_name = info['OSName']
            platversion = info['platversion']
            name = info['Name']
            lob = info['LOB']
        except Exception as e:
            print(f"##### group_inventory - WARNING - {e} - {info}")

        if 'Amazon Linux' in os_name:
            if arch == 'AMD':
                if platversion in ['2023','2']:
                    instance_os_type['amazon_linux_amd_2'].append(ip+"     #"+name+" LOB - "+lob)
                else:
                    instance_os_type['amazon_linux_amd_below_2'].append(ip+"     #"+name+" LOB - "+lob)
            else:
                if platversion in ['2023','2']:
                    instance_os_type['amazon_linux_arm_2'].append(ip+"     #"+name+" LOB - "+lob)
                else:
                    instance_os_type['amazon_linux_arm_below_2'].append(ip+"     #"+name+" LOB - "+lob)
        elif 'Windows' in os_name:
            instance_os_type['windows'].append(ip+"     #"+name+" LOB - "+lob)

        else:
            if arch == 'AMD':
                instance_os_type['linux_amd'].append(ip+"     #"+name+" LOB - "+lob)
            else:
                instance_os_type['linux_arm'].append(ip+"     #"+name+" LOB - "+lob)
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
