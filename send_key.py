import boto3
import json
def copy_public_key_to_instance(public_key_path, instance_ips):
    with open(public_key_path, 'r') as public_key_file:
        public_key = public_key_file.read()

    ssm_client = boto3.client('ssm',region_name='ap-southeast-1')

    for instance_ip in instance_ips:
        document_name = 'CopySSHPublicKeyDocument'
        document_content = f'''{{
            "schemaVersion": "2.2",
            "description": "Copy SSH Public Key to Authorized Keys",
            "mainSteps": [
                {{
                    "action": "aws:runShellScript",
                    "name": "copy_ssh_key",
                    "inputs": {{
                        "runCommand": [
                            "echo \'{public_key}\' >> /root/.ssh/authorized_keys"
                        ]
                    }}
                }}
            ]
        }}'''

        response = ssm_client.create_document(
            Name=document_name,
            DocumentType='Command',
            Content=json.dumps(document_content),
        )

        instance_id = get_instance_id_from_ip(instance_ip)

        if instance_id:
            response = ssm_client.send_command(
                InstanceIds=[instance_id],
                DocumentName=document_name,
                DocumentVersion='$DEFAULT',
                TimeoutSeconds=3600,
            )

            print(f"Copying public key to {instance_ip}... Command ID: {response['Command']['CommandId']}")
        else:
            print(f"Instance with IP {instance_ip} not found. Skipping...")

def get_instance_id_from_ip(instance_ip):
    ec2_client = boto3.client('ec2')
    response = ec2_client.describe_instances(
        Filters=[
            {
                'Name': 'private-ip-address',
                'Values': [instance_ip]
            },
        ],
    )

    instances = response['Reservations']

    if instances:
        return instances[0]['Instances'][0]['InstanceId']
    else:
        return None

if __name__ == "__main__":
    public_key_path = "/root/.ssh/id_rsa.pub"  # Update this with your actual public key path
    instance_ips = ["10.159.130.10", "10.159.161.31"]  # Add the IP addresses of the instances you want to update

    copy_public_key_to_instance(public_key_path, instance_ips)
