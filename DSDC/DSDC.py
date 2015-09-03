#! /usr/bin/python

import subprocess;
import time;
from datetime import datetime

def getCPU_util():
	"""1. Collects CPU utilization of each server via snmpwalk.
	2. If the average utilization of all the server is higher than uppper threshold, it sends command to turn on the standby server.
	If the average utilization of all the server is lower than the lower threshold, it sends command to turn off the standby server.
	3. returns string in following format:  
			['13:48:03', 12, 2, 15, 12, 2, 0, 8, 60, 40],
			['hh:mm:ss', serv1Util, serv2Util, serv3Util, serv4Util, serv5Util, servStandByUtil, AvgUtil, UpperThreshold, LowerThreshold],
	"""

	snmp_community = "DSDC"
	# webservers
	ip_addr = ["192.168.122.101", "192.168.122.102", "192.168.122.103", "192.168.122.104", "192.168.122.105", "192.168.122.106"]

	# Python interacts with Shell CMD
	p = subprocess.Popen("date", stdout=subprocess.PIPE, shell=True)
	(date, err) = p.communicate()

	# Find time
	i=0;
	for word in date.split():
		i+=1;
		if ":" in word:
			t_int = [word]
	# print "time inteval: ", t_int

	# get CPU util from all IP
	n = 1;	cpu_util_sum=0;
	for ip in ip_addr:
		n += 1; #print n;
		print "snmpwalk ip: ", ip
		CMD = "snmpwalk -v2c -c " + snmp_community + " " + ip + " -On .1.3.6.1.2.1.25.3.3.1.2 | tail -n 1 | cut -c 40-42"
		p = subprocess.Popen(CMD, stdout=subprocess.PIPE, shell=True)
		(output, err) = p.communicate()
		
		# Handles case when the server output is nothing  - when www-6 is turned off.
		if output=="":
			#print "--- STATUS: www-6 DOWN ---: input=null"
			print "--- STATUS: www-6 DOWN ---"
			output = "0\n";

		if output=="nce\n":
			#print "--- STATUS: www-6 DOWN ---: input=nce"
			print "--- STATUS: www-6 DOWN ---"
			output = "0\n";	
	
		t_int.append(output.rstrip('\n'))
		cpu_util_sum += int(output);

	# calculate average CPU Util and add as the last entry of the t_int list
	print "www-6 cpu util: ", t_int[5]
	
	# case www-6 is running and has a decent amount of utilization.  
	# This was needed for graphing to prevent avg value from spiking.
	if t_int[6] > "15":
		avg_cpu_util = cpu_util_sum/(len(ip_addr))
		print "avg: ", avg_cpu_util

	# case www-6 is not running
	else :
		avg_cpu_util = cpu_util_sum/(len(ip_addr)-1)
		print "Avg. CPU Utilization including www-6: ", avg_cpu_util

	t_int.append(str(avg_cpu_util))

	# Dual threashold to prevent server on/off flapping
	threshold_ON = 60
	threshold_OFF = 40
	t_int.append(str(threshold_ON))
	t_int.append(str(threshold_OFF))


	# Check to see if the www-6 is up.
	if avg_cpu_util > threshold_ON:
		# turn on www-6
		print "--- ACTION: Starting Server www-6 ---"
		CMD = "ssh kyurim@192.168.122.1 -t sudo virsh start SNA-www6-CentOS_6.5-x86_64"
		p = subprocess.Popen(CMD, stdout=subprocess.PIPE, shell=True)
		(output, err) = p.communicate()

	if avg_cpu_util < threshold_OFF:
		# turn off www-6	
		print "--- ACTION: Stopping Server www-6 ---"
		CMD = "ssh kyurim@192.168.122.1 -t sudo virsh shutdown SNA-www6-CentOS_6.5-x86_64"
		p = subprocess.Popen(CMD, stdout=subprocess.PIPE, shell=True)
		(output, err) = p.communicate()

	# convert list into strings
	data = ", ".join(t_int)
	data = "['"+ data[:8] + "'" + data[8:] + "],"
	return data



def timePause(time_in, t0):
	"""Creates pause of x sec for each iteration.
	"""
        t1 = datetime.now()
        t_diff = (t1-t0).seconds
        print "t_diff = t1-t0 =", t_diff

        if t_diff <2:
        	print "Time Scale: "+ "=" + str(time_in) + " (" +str(time_in)+ " sec)"
                print ">>>time.sleep(" +str(time_in)+ ")"; time.sleep(time_in);

	else:
                print "Time Scale: "+ "=" * t_diff + " ("+str(t_diff)+ " sec)"


def generateHtmlList():
	"""creates a list of CPU utilization values to be inserted into a html file.
	"""
	#create maximum of n datapoints
        if len(html_list) > max_data_point-1:
                del html_list[1];


        # append the latest SNMP CPU Util onto this list
        curr_cpu_util = getCPU_util()
        html_list.append(curr_cpu_util)

        # update the Header
        print "curr_cpu_util:  " + curr_cpu_util

        # print CPU Utilization on legend
        i=0; cpu = [];
        for word in curr_cpu_util.split():
                #print i,"-split word: ", word
                cpu.append(word.rstrip(','));
                i+=1

        html_list[0] = "['Time', 'www-1:  "+cpu[1]+ \
                            "%', 'www-2:  "+cpu[2]+ \
                            "%', 'www-3:  "+cpu[3]+ \
                            "%', 'www-4:  "+cpu[4]+ \
                            "%', 'www-5:  "+cpu[5]+ \
                            "%', 'www-6:  "+cpu[6]+ \
                            "%', 'Avg Sys Util:  "+cpu[7]+ \
                            "%', 'Threshold-ON', 'Threshold-OFF'],"

def updateWebPage():
        text_file = open("/var/www/html/index_top.html")
        top = text_file.readlines();
        text_file.close();

        text_file = open("/var/www/html/index_bottom.html")
        bottom = text_file.readlines();
        text_file.close();

        wr_file = open("/var/www/html/index.html", 'w')
        for l in top:
                l = l.rstrip('\n')
                wr_file.write("%s\n" % l)

        for l in html_list:
                print "html list", l
                wr_file.write("%s\n" % l)

        for l in bottom:
                l = l.rstrip('\n')
                wr_file.write("%s\n" % l)


# Main
#if __name__ == "__main__":
def main():
	while True:
		t_now = datetime.now()	
		print "--------------------------------------------------------------------------------------------";
		generateHtmlList()
		updateWebPage()

		# Ensure this process runs at even x sec interval
		time_increment = 6;	# sec
		timePause(time_increment, t_now)



html_list = []
max_data_point = 45    # number of max time increment in a graph.

if __name__ == "__main__":
	main()
