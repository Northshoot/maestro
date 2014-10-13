#!/usr/bin/python
import boto.ec2
region='eu-west-1'

def getReservation(instance=None):
	conn = boto.ec2.connect_to_region(region)
	reservation=[]
	if instance:
		reservation = conn.get_all_instances(instance_ids=[instance])
	else:
		reservation = conn.get_all_instances()
	return reservation

if __name__ == '__main__':
	res= getReservation('i-c73fbf88')
	print res
	for i in res[0].instances:
	    print i.public_dns_name
