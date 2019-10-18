import boto3
import botocore
import json


s3 = boto3.resource('s3')

def extract(key, value):
    if(type(value) == str):
        result = "{'"+key+"' : '"+value+"'}"
        print(result)
        #obj[key]=value
        return

    t = 0
    if(type(value) == list):
        for i in value:
            extract(key+"_"+str(t),i)
            t = t + 1
        return

    if(type(value) == dict):
        for i in value.keys():
            if key:
                key_i = key+"_"+i
            else:
                key_i = i
            extract(key_i,value[i])
        return


def parse_s3_remote_data(bucket_name, object_key, pathname):

    try:
        s3.Bucket(bucket_name).download_file(object_key, pathname)

        with open(pathname) as f:
            dat = f.read()
            json_data = json.loads(dat)

    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            print("The object does not exist.")
        else:
            raise

    return json_data


def empty_s3_bucket(bucket_name):

    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket_name)
    # suggested by Jordon Philips
    bucket.objects.all().delete()