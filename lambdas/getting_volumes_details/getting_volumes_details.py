import csv
from os import environ
import boto3
import datetime

s3 = boto3.resource('s3', region_name='ap-southeast-1')
today = datetime.datetime.now()
files = "{}{}{}".format("Unencrypted-ebs-details",today,".csv")
regions = ["ap-southeast-1","ap-northeast-1"]
filename = "{}/{}".format(environ.get("AUTOMATION_BRANCH_S3_PREFIX"),files)
filepath = '/tmp/Unencrypted-ebs-details.csv'
upload_bucket= environ.get("AUTOMATION_BUCKET")

roles =[
    # "arn:aws:iam::234:role/ABC_CloudOps" #testing
    "arn:aws:iam::123:role/PipelineProvisioning", #poc1
	"arn:aws:iam::123:role/PipelineProvisioning", #poc2
    "arn:aws:iam::123:role/PipelineProvisioning", #poc3
    "arn:aws:iam::1232:role/PipelineProvisioning", #poc4
    "arn:aws:iam::123:role/PipelineProvisioning", #poc5
    "arn:aws:iam::234:role/PipelineProvisioning", #dev1
    "arn:aws:iam::234:role/PipelineProvisioning", #dev2
    "arn:aws:iam::2343:role/PipelineProvisioning", #dev3
    "arn:aws:iam::2343:role/PipelineProvisioning", #dev4
    "arn:aws:iam::2343:role/PipelineProvisioning", #dev5
    "arn:aws:iam::2343:role/PipelineProvisioning",  #Automated Prod
    "arn:aws:iam::2343:role/PipelineProvisioning",  #SemiAutomated Prod
    "arn:aws:iam::2343:role/PipelineProvisioning",	#Services Prod
    "arn:aws:iam::2343:role/PipelineProvisioning",	#Automated Nonprod
    "arn:aws:iam::343:role/PipelineProvisioning",	#SemiAutomated Nonprod
    "arn:aws:iam::34:role/PipelineProvisioning",	#NonServices Nonprod
    "arn:aws:iam::234:role/PipelineProvisioning"	#master
	
]
def lambda_handler(event, context):
    ebs_details(roles)

def get_credentials(assume_role):
    
    try:
        sts_client = boto3.client('sts')
        assumedRoleObject = sts_client.assume_role(RoleArn=assume_role,RoleSessionName="AssumeRoleSession")
        print (assumedRoleObject['Credentials'])
        return assumedRoleObject['Credentials']
    except Exception as e:
        print("Error during STS assume role %s" % e)


def client_connection(service,credentials,region):
    try:
        return boto3.client(service,aws_access_key_id = credentials['AccessKeyId'],aws_secret_access_key = credentials['SecretAccessKey'],
                                 aws_session_token = credentials['SessionToken'],region_name= region)
    except Exception as e:
        print (e)
        
def ebs_details(roles):    
    
    volume_dict = {}
    for role in roles:
        # print (role)
        account = role.split(":")[4]
        for region in regions:
            credentials=get_credentials(role)
            client = client_connection('ec2', credentials,region)
            # client = boto3.client('ec2', aws_access_key_id = "ASIA3BTYALRG3VWPUQHU",aws_secret_access_key = "c+FQ6Lod2MAAQmi+WJN1dobrX96b8klE9w6rdwhJ",
                                #  aws_session_token = "FQoGZXIvYXdzEKP//////////wEaDO4K9pgtDalw/IvRNSL9Ah+jVQbQ5MiFZK/wGB1IuVfpZM/DHWSI7tB7iMwaUhdSByhwsc+GeylEh5P7o8/DAENhF40D1bqZYs4yNkOQ4ECv42bo+DcSr+8lZGwKnmUe29T7jL5o8SKUeRQV1PWEBNKoWjs0L+PnBCD8tvEEASwQ9lHsD9L1XP0yRLiTSehGzBflJKMSCJflNle7ALI5QYjlBhatNTX52P8j8vZmN0vX3xgkiVS0UU1Zx1fny/tK40eQug2aTunOTMh1+uJhDYC/5v7AjDNz+8TQ5oN0JA9yKSUUwlIatZtT7T9GIyNNeIHdABmkD/9tkPraoXw0uPTtmteb0k0VyNy1JoZx7QIbgdu9PX3OSybszI83+VE8QiPKiVBSRy/DuxO6AWehPi3pcJGOgFLm8NggM0lCrlNOzP/IH8EHV4ijQ79Oyqst14Idg8HMYnevPzth1DBmPVLMQuzvePZPePHFuFScQoqxtDOwEoNTZz63lQ0AlbkwD4HSYOEnIRe2AsRk7SiC74zrBQ==",region_name= region)

            volumes = client.describe_volumes()
            snapshots = client.describe_snapshots(OwnerIds=['self'])

            volume_types_map = { u'standard' : u'Standard/Magnetic', u'io1' : u'Provisioned IOPS (SSD)', u'gp2' : u'General Purpose SSD', u'st1' : u'Throughput Optimized HDD', u'sc1' : u'Cold HDD'}
            volume_dict [region] = {}
            for vol in volumes['Volumes']:
                try:
                    name = vol['Tags']    
                except:
                    name = u''    
                try:
                    iops = vol['Iops']    
                except:
                    iops = 0                    
                if not vol['Attachments'] :
                    instance_id = 'Not Attached'
                    device = 'N/A'
                    volume_dict[region][vol['VolumeId']] = { 'name' : name, 
                                                'size' : vol['Size'],
                                                
                                                'type' : volume_types_map[vol['VolumeType']],
                                                'iops' : iops,
                                                'orig_snap' : vol['SnapshotId'],
                                                'encrypted' : vol['Encrypted'],
                                                'instance' : instance_id,
                                                'device' : device,
                                                'num_snapshots' : 0,
                                                'first_snap_time' : u'',
                                                'first_snap_id' : u'N/A',
                                                'last_snap_time' : u'',
                                                'CreateTime' : vol['CreateTime'],
                                                "Account" : account
                                                }
                else:
                    for vols in vol['Attachments']:
                        if vols['State'] == 'attached':
                            instance_id = vols['InstanceId']
                            device = 'N/A'
                        else:
                            instance_id = 'N/A'
                            device = 'N/A'
                   
                    volume_dict[region][vol['VolumeId']] = { 'name' : name, 
                                                'size' : vol['Size'],
                                                
                                                'type' : volume_types_map[vol['VolumeType']],
                                                'iops' : iops,
                                                'orig_snap' : vol['SnapshotId'],
                                                'encrypted' : vol['Encrypted'],
                                                'instance' : instance_id,
                                                'device' : device,
                                                'num_snapshots' : 0,
                                                'first_snap_time' : u'',
                                                'first_snap_id' : u'N/A',
                                                'last_snap_time' : u'',
                                                'CreateTime' : vol['CreateTime'],
                                                "Account" : account
                                                }
        write_csv(volume_dict)


def write_csv(volume_dict):
    with open(filepath, 'a+') as f:
        heading = ['Account','Region','volume ID','Volume Name','Volume Type','iops','Size (GiB)', \
                      'Created from Snapshot','Attached to','Device','Encrypted','Number of Snapshots', \
                      'Earliest Snapshot Time','Earliest Snapshot','Most Recent Snapshot Time','CreateTime']
        writer = csv.writer(f)
        writer.writerow(heading)
        volume_dic = list(volume_dict)
        for region in volume_dict:
            for volume_id in volume_dict[region]:
                volume = volume_dict[region][volume_id]
                writer.writerow ([volume['Account'],region, volume_id, volume['name'],volume['type'],volume['iops'],volume['size'], \
                        volume['orig_snap'],volume['instance'],volume['device'],volume['encrypted'], \
                        volume['num_snapshots'],volume['first_snap_time'],volume['first_snap_id'], \
                        volume['last_snap_time'],volume['CreateTime']])
        f.close ()
            
    s3.Object(upload_bucket, filename).put(Body=open(filepath, 'rb'))
    # print ("Object uploaded")

# if __name__ == '__main__':
#     lambda_handler("event", "context")
