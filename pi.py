import time
import threading
import sys
import RPi.GPIO as gpio
import paho.mqtt.client as mqtt
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
from email import encoders
import picamera
import os
import datetime

############### Settings ##################
client = mqtt.Client("EDEN_PI", clean_session=False)
client.username_pw_set("Cloud instance name", "Password")
#weather = Weather(unit=Unit.CELSIUS)
#location = weather.lookup_by_location('Toronto')
#condition = location.condition
#temperature = condition.temp

subTopic = "GPIO/instructions"
pubTopic = "GPIO/Data"
path = "/home/pi/Desktop/"    #path of image file
email = "User email"

pump = 18
trig = 20
echo = 21
moist = 12
flag = True


############### Settings ##################

#Setup ports with output direction
def gpioSetup():
    gpio.setwarnings(False)
    gpio.setmode(gpio.BCM)
    #Pump power
    gpio.setup(pump, gpio.OUT,initial=0)
    #Ultrasonic sensor 
    gpio.setup(trig, gpio.OUT, initial=0)
    gpio.setup(echo, gpio.IN)
    #Humidity sensor
    gpio.setup(moist, gpio.IN)
    
def takePicture():
    global path
    camera = picamera.PiCamera()            
    camera.capture(path+"plants.jpg")                    
    camera.close()                          
#end def

def sendPicture():
    global path
    server = smtplib.SMTP_SSL('smtp.gmail.com',465)   
    #eden garden gmail  
    me = ""    
    #and password                                        
    password = ""                                       
    server.login(me,password)                          

    image = MIMEImage(open(path+"plants.jpg",'rb').read(),name="plants.jpg")     

    msg = MIMEMultipart()                                           

    msg['Subject'] = "Picture of your plants"                       
    msg['From'] = me                                                
    msg['To'] = email                                               

    msg.attach(image)                                       

    server.sendmail(me,msg['To'],msg.as_string())           

    server.quit()                                          
        
    os.remove(path+"plants.jpg")                                         

#Funcion to calculate water level    
def water():
    global flag
    try:
        while True:
            gpio.output(trig,False)
            time.sleep(1)
                
            gpio.output(trig,True)
            time.sleep(0.00001)
            gpio.output(trig,False)
                
            while gpio.input(echo) == 0:
                    pulse_start = time.time()
                    
                
            while gpio.input(echo) == 1:
                    pulse_end = time.time()
                    
                
            pulse_duration = pulse_end - pulse_start
            distance = pulse_duration * 17150
            distance = round(distance,2)
            
			#find percentage remaining based pulse duration and container size
            percentage = int(((distance - 4.5)*100)/9.8)
            
			#Check for oddities and only publish the ones that are less than 100%
            if percentage < 130:
                if percentage <=0:
                    percentage = 0
                elif percentage >=100:
                    percentage = 100
                client.publish(pubTopic,payload="wl"+str(100-percentage),qos=0)
                
            #Check last watering status everyday at 10am     
            if datetime.datetime.now().hour == 10:
                notify(flag)
                flag = False
                
    except Exception:
        print(str(Exception))

#If date delt is 3 or more then send ser notification        
def notify(flag):
    global email
    if flag:
        #Open log file
        file = open('log.txt','r')
        month= file.readline()
        day = file.readline()
		
		#Calculate delta
        last = datetime.datetime(2019,int(month),int(day))
        date = datetime.datetime.today()
        substract = date - last
        
		#Email
        if int(substract.days) >= 3:
            msg = MIMEMultipart()
            msg["From"] = me
            msg["To"] = email
            msg["Subject"] = "Eden System Notification"
            
            msg.attach(MIMEText("Your plants have not been watered in more than three days!",'plain'))
            
            server = smtplib.SMTPserver = smtplib.SMTP_SSL('smtp.gmail.com',465)
            server.login(me,"tpj_655_eden")
            
            server.sendmail(me,msg['To'],msg.as_string())
            server.quit()
            print("notified")
        
        file.close()
    


#Pump activation 
def activate():
    
	#log the date it was activated
    file = open('demo.txt','w')
    file.write(str(datetime.datetime.today().month)+"\n")
    file.write(str(datetime.datetime.today().day))
    file.close()
    
	#Create pwm object
	pwmPump = gpio.PWM(pump,1000)
    DC = 0
    pwmPump.start(DC)
    
    #Increment solowly the dty cycle when started
    while DC <= 99:
        DC += 33
        pwmPump.ChangeDutyCycle(DC)
        time.sleep(1)
    time.sleep(3)
    pwmPump.stop()
    gpio.output(pump,0)   
   
#Publish output from humidity sensor
def humidity(moist):
    time.sleep(0.1)
    if gpio.input(moist):
        client.publish(pubTopic, payload="m1", qos=0)
        #Dry
        print("dry")
    else:
        client.publish(pubTopic, payload="m0", qos=0)
        #wet
        print("wet")


# The callback for when the client connects
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe(subTopic)

# Checks message from published topic to instruct GPIOs
def on_message(client, userdata, msg):
    global email
    message = msg.payload.decode(encoding='UTF-8')
    if message == "sync":
        #Run sync function
        print("Syncing Data!")
    elif "pic" in message:
	#Run camera function
        takePicture()
        sendPicture()
        print("Picture taken and sent to ", email)
    elif "pump" in message or "on" in message:
        print("Watering system is on!")
        activate()
    elif "@" in message:
        email = message
        print("Email changed to "+email)
    else:
        print("Unknown message!")


#Connection events
client.on_connect = on_connect
client.on_message = on_message
client.connect("m15.cloudmqtt.com", 13159, 60)

#Enable GPIO configuration
gpioSetup()

state = bin(gpio.input(moist))
gpio.add_event_detect(moist, gpio.BOTH, bouncetime=300)
gpio.add_event_callback(moist,humidity)    

thread = threading.Thread(target=water)
thread.daemon = True
thread.start()

# Infinite loop to keep program running until it is closed
client.loop_forever()

