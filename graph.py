#!/usr/bin/python

#Imports
import pyowm
import shutil
import sys
import os
import time
import rrdtool
import subprocess
import Adafruit_DHT as dht
import smtplib
import datetime
from twython import Twython


#Command to create RRDFILE.  Run this via CLI
#rrdtool create /home/pi/bucket.rrd \
#--step 300 \
#DS:temp:GAUGE:600:0:120 \
#DS:humi:GAUGE:600:0:100 \
#DS:ODTemp:GAUGE:600:0:120 \
#DS:ODHumi:GAUGE:600:0:100 \
#RRA:AVERAGE:0.5:1:600 \
#RRA:AVERAGE:0.5:6:700 \
#RRA:AVERAGE:0.5:24:775 \
#RRA:AVERAGE:0.5:288:797 \
#RRA:MIN:0.5:1:600 \
#RRA:MIN:0.5:6:700 \
#RRA:MIN:0.5:24:775 \
#RRA:MIN:0.5:144:797 \
#RRA:MAX:0.5:1:600 \
#RRA:MAX:0.5:6:700 \
#RRA:MAX:0.5:24:775 \
#RRA:MAX:0.5:288:797







#Twitter API Keys and stuffs
consumer_key        = 'YOUR TWITTER KEY' #EDIT THIS LINE
consumer_secret     = 'YOUR TIWTTER SECRET KEY' #EDIT THIS LINE
access_token        = 'YOUR TWITTER ACCESS TOKEN' #EDIT THIS LINE
access_token_secret = 'YOUR TWITTER ACCESS TOEKN SECRET' #EDIT THIS LINE
api = Twython(consumer_key,consumer_secret,access_token,access_token_secret)

#Get weather info from openweathermap
owm = pyowm.OWM('YOUR OPEN WEATHERMAP API KEY') #EDIT THIS LINE
observation = owm.weather_at_id(YOUR LOCATION ID) #EDIT THIS LINE
w = observation.get_weather()


#Time Stuff for Twitter
time1 = datetime.datetime.now()
hour = time1.strftime("%H:%M")
pictime = time1.strftime("%m-%d-%Y-%H:%M")


def read():
#Read from DHT11 on Pin4
	global h
	global t
	h,t = dht.read_retry(dht.DHT11, 4)
	t = t * 9/5.0 + 32
	check()

def check():
#Error Checking.  Sometimes the sensor will read 50some degree's and 140something humdity.
	global h
	global t
	if h > 100:
		time.sleep(5)
		read()

read()


ODTemp = w.get_temperature('fahrenheit').get('temp')
ODHumi = w.get_humidity()


def Validate(value):
  if value == None:
    return ":U"
  else:
    return ":{}".format(value)

#Email Alerts
if t > 83:
	server = smtplib.SMTP('smtp.gmail.com', 587) #EDIT THIS LINE IF YOU DONT USE GMAIL  Need to allow less secure apps on your gmail account for this to work https://support.google.com/accounts/answer/6010255?hl=en
	server.starttls()
	server.login("YOUR GMAIL LOGIN", "YOUR GMAIL PASSWORD") #EDIT THIS LINE
	str(t)
	server.sendmail("YOUR FROM EMAIL ADDRESS", "YOUR TO EMAIL OR SMS ADDRESS", "The current temp is " + str(t)) #EDIT THIS LINE
	server.quit()
#End Email Alerts

rdata = "N" + Validate(t) + Validate(h)  + Validate(ODTemp) + Validate(ODHumi)
fileRrdtool = "/home/pi/bucket.rrd" 

#update rrd file and then graph it
subprocess.Popen(["/usr/bin/rrdtool","update",fileRrdtool,rdata])
for sched in ['daily', 'weekly', 'monthly', 'yearly']:
    if sched == 'weekly':
        period = 'w'
    elif sched == 'daily':
        period = 'd'
    elif sched == 'monthly':
        period = 'm'
    elif sched == 'yearly':
	period = 'y'
    ret = rrdtool.graph( "/var/www/html/bucket-%s.png" %(sched), "--start", "-1%s" %(period), "--watermark=YOUR WATER MARK", "--title=YOUR TITLE", "--upper-limit=100", "--lower-limit=0", "--rigid", "--base=1000", "--alt-autoscale-max", "--height=160", "--width=600", "--slope-mode", "--vertical-label=YOUR VERTICAL LABEL", #EDIT THIS LINE
 "DEF:temp=bucket.rrd:temp:AVERAGE",     
 "DEF:humi=bucket.rrd:humi:AVERAGE",     
 "DEF:ODTemp=bucket.rrd:ODTemp:AVERAGE",
 "DEF:ODHumi=bucket.rrd:ODHumi:AVERAGE",
 "LINE2:temp#FF0000:Temp        ",
 "GPRINT:temp:LAST:Current\:%2.2lf",
 "GPRINT:temp:AVERAGE:Average\:%2.2lf",
 "GPRINT:temp:MAX:Max\:%2.2lf \\n",
 "LINE2:humi#0000FF:Humi        ",
 "GPRINT:humi:LAST:Current\:%2.2lf",
 "GPRINT:humi:AVERAGE:Average\:%2.2lf",
 "GPRINT:humi:MAX:Max\:%2.2lf\\n",
 "LINE1:ODTemp#33FF49:Outdoor Temp",
 "GPRINT:ODTemp:LAST:Current\:%2.2lf",
 "GPRINT:ODTemp:AVERAGE:Average\:%2.2lf",
 "GPRINT:ODTemp:MAX:Max\:%2.2lf \\n",
 "LINE1:ODHumi#FF33F6:Outdoor Humi",
 "GPRINT:ODHumi:LAST:Current\:%2.2lf",
 "GPRINT:ODHumi:AVERAGE:Average\:%2.2lf",
 "GPRINT:ODHumi:MAX:Max\:%2.2lf \\n",)

#Post to Twitter
if hour in {"01:00", "05:00", "09:00", "13:00", "17:00", "21:00"}:
	message = "YOUR TWITTER MESSAGE" #EDIT THIS LINE
	with open ('/var/www/html/bucket-daily.png', 'rb') as photo:
		api.update_status_with_media(status=message, media=photo)
#Take pic with webcam
os.system("fswebcam  -i 0 -d v4l2:/dev/video0 --jpeg 95 --save /var/www/html/plant.jpg -F 10 -S 20 -r 1280x720 --set sharpness=200")

#Copy current picture to other folder with datetime as the file name.
current = "/var/www/html/plant.jpg"
newname ="/home/pi/pics/" +pictime+ ".jpg"
shutil.copyfile(current, newname)

