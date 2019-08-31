import csv
from os import environ
import boto3

s3 = boto3.resource('s3', region_name='ap-southeast-1')
ses = boto3.client('ses')

filename = "{}/{}".format(environ.get("AUTOMATION_BRANCH_S3_PREFIX"),"Trusted-Advisor-SG-details.csv")
filepath = '/tmp/Trusted-Advisor-SG-details.csv'
upload_bucket= environ.get("AUTOMATION_BUCKET")
roles =[
    "arn:aws:iam::2343:role/PipelineProvisioning", #poc1
	"arn:aws:iam::2343:role/PipelineProvisioning", #poc2
    "arn:aws:iam::2343:role/PipelineProvisioning", #poc3
    "arn:aws:iam::234:role/PipelineProvisioning", #poc4
    "arn:aws:iam::2343:role/PipelineProvisioning", #poc5
    "arn:aws:iam::2343:role/PipelineProvisioning", #dev1
    "arn:aws:iam::2343:role/PipelineProvisioning", #dev2
    "arn:aws:iam::2343:role/PipelineProvisioning", #dev3
    "arn:aws:iam::2343:role/PipelineProvisioning", #dev4
    "arn:aws:iam::2343:role/PipelineProvisioning", #dev5
    "arn:aws:iam::343:role/PipelineProvisioning",  #Automated Prod
    "arn:aws:iam::234:role/PipelineProvisioning",  #SemiAutomated Prod
    "arn:aws:iam::234:role/PipelineProvisioning",	#Services Prod
    "arn:aws:iam::2343:role/PipelineProvisioning",	#Automated Nonprod
    "arn:aws:iam::2343:role/PipelineProvisioning",	#SemiAutomated Nonprod
    "arn:aws:iam::234:role/PipelineProvisioning",	#NonServices Nonprod
    "arn:aws:iam::2343:role/PipelineProvisioning"	#master
	
]
def lambda_handler(event, context):
    trusted_advisor(roles)

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
                                 aws_session_token = credentials['SessionToken'],region_name=region)
    except Exception as e:
        print (e)
        
def trusted_advisor(roles):    
    
    sg_from_instance_all_account = {}
    sg_from_ta_all_account = {}
    for role in roles:
        print (role)
        account = role.split(":")[4]
        credentials=get_credentials(role)
        client = client_connection('support', credentials,"us-east-1")
        print (client)
        response = client.describe_trusted_advisor_checks(language="en")
        print ("PRINTING",response['checks'])
        
        sg_from_instance = get_instance_sg(credentials)
        check_id = ''
        for check in response['checks']:
            if check['name'] == 'Security Groups - Unrestricted Access':
                results = client.describe_trusted_advisor_check_result(checkId=check['id'])
                # results = {"result": {"checkId": "1iG5NDGVre", "timestamp": "2019-08-08T01:35:24Z", "status": "error", "resourcesSummary": {"resourcesProcessed": 44, "resourcesFlagged": 11, "resourcesIgnored": 0, "resourcesSuppressed": 0}, "categorySpecificSummary": {"costOptimizing": {"estimatedMonthlySavings": 0.0, "estimatedPercentMonthlySavings": 0.0}}, "flaggedResources": [{"status": "error", "region": "ap-southeast-1", "resourceId": "ug8drhpfxKMoDesjpIPhDLMEqfzYf__qd1za-vZu-bk", "isSuppressed": False, "metadata": ["ap-southeast-1", "ACIAnyWhere-rCAPICInfraSecurityGroup-1T4L3577GG5OZ", "sg-0d366d7677d7d714b (vpc-0c2041b3272759712)", "-1", None, "Red", "0.0.0.0/0"]}, {"status": "error", "region": "ap-southeast-1", "resourceId": "Cgbg3zsZxAATancQV5kjhOr7LWll1QKqrcigYze99Cw", "isSuppressed": False, "metadata": ["ap-southeast-1", "Web_Server_SG", "sg-0614a92877f0ed1eb (vpc-03752f6f0f8bcfef8)", "tcp", "22", "Red", "0.0.0.0/0"]}, {"status": "error", "region": "ap-southeast-1", "resourceId": "KobwEaeWwdYDLsruli6vTlAGn3EQt7luM_V6zK6wV5w", "isSuppressed": False, "metadata": ["ap-southeast-1", "SG-Mayank-Nauni", "sg-08399de879dbb0e67 (vpc-f503c692)", "tcp", "1521", "Red", "0.0.0.0/0"]}, {"status": "error", "region": "ap-southeast-1", "resourceId": "XJURXkGjqrre4cVqac-QJyvMADdcDqHAF5AV5IXTZC8", "isSuppressed": False, "metadata": ["ap-southeast-1", "SG-Mayank-Nauni", "sg-08399de879dbb0e67 (vpc-f503c692)", "tcp", "3389", "Red", "0.0.0.0/0"]}, {"status": "error", "region": "ap-southeast-1", "resourceId": "_Za8i7u-EoZ5mGT-2BmB144wPM8eUAWd75_wvvvOlUs", "isSuppressed": False, "metadata": ["ap-southeast-1", "launch-wizard-5", "sg-09354a9105a6fbc34 (vpc-03752f6f0f8bcfef8)", "tcp", "3389", "Red", "0.0.0.0/0"]}, {"status": "error", "region": "ap-southeast-1", "resourceId": "dpX12aWiHOzYocxJ5YiM9j2HztF5O9r05biN5aKxX68", "isSuppressed": False, "metadata": ["ap-southeast-1", "launch-wizard-1", "sg-0a795efbde3493f9e (vpc-f503c692)", "tcp", "1521", "Red", "0.0.0.0/0"]}, {"status": "error", "region": "ap-southeast-1", "resourceId": "oB7waQcynHN7-9CI1GTF0CKH714FIWXT5SsKEr5SUw8", "isSuppressed": False, "metadata": ["ap-southeast-1", "launch-wizard-1", "sg-0a795efbde3493f9e (vpc-f503c692)", "tcp", "22", "Red", "0.0.0.0/0"]}, {"status": "error", "region": "ap-southeast-1", "resourceId": "leYVPPilE1ByhFncUIh9ikXr5rAvpcWpucMdTETVHfI", "isSuppressed": False, "metadata": ["ap-southeast-1", "ACIAnyWhere-rCAPICOOBSecurityGroup-ROII1BTWOTRB", "sg-0abcca7d0c0afbf7c (vpc-0c2041b3272759712)", "tcp", "22", "Red", "0.0.0.0/0"]}, {"status": "error", "region": "ap-southeast-1", "resourceId": "2yQSWMzaYzMPXMyhlnsyxSCFAicsCTa_djjHH82gSYQ", "isSuppressed": False, "metadata": ["ap-southeast-1", "SSH_Allowed_Any", "sg-0d8e524775c1750e4 (vpc-03752f6f0f8bcfef8)", "tcp", "22", "Red", "0.0.0.0/0"]}, {"status": "error", "region": "ap-southeast-1", "resourceId": "BalrzecWfUo9x7lY8vZZUBMyJveu4lXImVwOaoKV3Ow", "isSuppressed": False, "metadata": ["ap-southeast-1", "launch-wizard-2", "sg-0f7f9ae0d6fdcaae6 (vpc-f503c692)", "tcp", "22", "Red", "0.0.0.0/0"]}, {"status": "error", "region": "ap-southeast-1", "resourceId": "fRSBYybe9k_D2onMOOw12xh3VZl_wUqlPzn9ysvNn3U", "isSuppressed": False, "metadata": ["ap-southeast-1", "launch-wizard-3", "sg-0fa18a118610f6986 (vpc-f503c692)", "tcp", "22", "Red", "0.0.0.0/0"]}]}, "ResponseMetadata": {"RequestId": "e4eb368a-6146-487a-9fbb-3acfd4176a7c", "HTTPStatusCode": 200, "HTTPHeaders": {"x-amzn-requestid": "e4eb368a-6146-487a-9fbb-3acfd4176a7c", "x-amzn-actiontrace": "amzn1.tr.956f3c57-ba6c-11e9-ac0d-0a5a06bc0000.0..txlAKm", "content-type": "application/x-amz-json-1.1", "content-length": "3091", "date": "Fri, 09 Aug 2019 06:11:53 GMT"}, "RetryAttempts": 0}}
                sg_from_instance_all_account[account] = parse_result(results, sg_from_instance)
    print(sg_from_instance_all_account)
    write_csv(sg_from_instance_all_account)


def parse_result(results, sg_from_instance):
    sg_from_ta = []
    for details in results['result']['flaggedResources']:
        sg_id = details['metadata'][2].split(' ')[0]
        details['metadata'].append(sg_id in sg_from_instance)
        sg_from_ta.append(details)
    return sg_from_ta


def write_csv(sg_from_instance_all_account):
    with open(filepath, 'w+') as f:
        heading = ["Account", "Region", "Status", "SG_Id", "SG_Name", "Port", "IP", "Is_Attached"]
        writer = csv.DictWriter(f,fieldnames=heading)
        writer.writeheader()
        for account in sg_from_instance_all_account:
            values = sg_from_instance_all_account[account]
            
            for value in values:
                dict = {
                    "Account": account,
                    "Region": value['metadata'][0],
                    "Status": value['metadata'][5],
                    "SG_Id": value['metadata'][2],
                    "SG_Name": value['metadata'][1],
                    "Port": value['metadata'][4],
                    "IP": value['metadata'][6],
                    "Is_Attached": value['metadata'][7]
                }
                # print (dict)
                writer.writerow(dict)

    s3.Object(upload_bucket, filename).put(Body=open(filepath, 'rb'))
    print ("Object uploaded")


def get_instance_sg(credentials):
    result = {}
    regions= ["ap-southeast-1","ap-northeast-1"]
    for region in regions:
        ec2 = client_connection('ec2', credentials,region )
        response = ec2.describe_network_interfaces()
    # print(response)
        for ins in response['NetworkInterfaces']:
            for group in ins['Groups']:
                print(group)
                list1 = result.get(group['GroupId'], [])
                list1.append(group['GroupName'])
                result[group['GroupId']] = list1
                # print ("sg_instance:",sg_instance)
    print(result)
    return result
