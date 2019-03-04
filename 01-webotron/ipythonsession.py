# coding: utf-8
import boto3
session = boto3.Session(profile_name='pythonAutomation')
aws s3 ls --profile pythonAutomation
s3 = session.resource('s3')
