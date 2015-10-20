#!/usr/bin/env python

import obd_io
import serial
import platform
import obd_sensors
from datetime import datetime
import time
import getpass
import pymysql


from obd_utils import scanSerial

class OBD_Recorder():
    def __init__(self, path, log_items):
        self.port = None
        self.sensorlist = []
        localtime = time.localtime(time.time())
        filename = path+"car-"+str(localtime[0])+"-"+str(localtime[1])+"-"+str(localtime[2])+"-"+str(localtime[3])+"-"+str(localtime[4])+"-"+str(localtime[5])+".log"
        self.log_file = open(filename, "w", 128)
        self.log_file.write("Time,RPM,MPH,Throttle,Load,Fuel Status\n");

        for item in log_items:
            self.add_log_item(item)

        self.gear_ratios = [34/13, 39/21, 36/23, 27/20, 26/21, 25/22]
        #log_formatter = logging.Formatter('%(asctime)s.%(msecs).03d,%(message)s', "%H:%M:%S")

    def connect(self):
        portnames = scanSerial()
        #portnames = ['COM10']
        print portnames
        for port in portnames:
            self.port = obd_io.OBDPort(port, None, 2, 2)
            if(self.port.State == 0):
                self.port.close()
                self.port = None
            else:
                break

        if(self.port):
            print "Connected to "+self.port.port.name
            
    def is_connected(self):
        return self.port
        
    def add_log_item(self, item):
        for index, e in enumerate(obd_sensors.SENSORS):
            if(item == e.shortname):
                self.sensorlist.append(index)
                print "Logging item: "+e.name
                break
            
    #Funcao que salva os dados em um .txt e salva no Banco de Dados       
    def record_data(self):
        if(self.port is None):
            return None    
				
        print "Logging started"
        
        while 1:
	    #Transformar tudo em string no Banco de Dados para melhor manipulacao na tela
            dbtime = None 
	    dbrpm = None
	    dbmph = None
	    dbthrottle = None
	    dbload = None
	    dbfuel = None
			
            localtime = datetime.now()
            current_time = str(localtime.hour)+":"+str(localtime.minute)+":"+str(localtime.second)+"."+str(localtime.microsecond)
            log_string = current_time
            results = {}
            for index in self.sensorlist:
                (name, value, unit) = self.port.sensor(index)
                log_string = log_string + ","+str(value)
                results[obd_sensors.SENSORS[index].shortname] = value;

            gear = self.calculate_gear(results["rpm"], results["speed"])
            log_string = log_string #+ "," + str(gear)
            self.log_file.write(log_string+"\n")
	    self.handle_data(log_string,dbtime,dbrpm,dbmph,dbthrottle,dbload,dbfuel)
	    #self.persist_data(dbtime,dbrpm,dbmph,dbthrottle,dbload,dbfuel)
			
			
			
	#Funcao que persiste dados no Banco		
    def persist_data(self,dbtime,dbrpm,dbmph,dbthrottle,dbload,dbfuel):
    	connection  = pymysql.connect(host='localhost',user='pi',passwd='raspberry',db='obd_database',charset='utf8')
	print "Inside persist_data"
	print "dbtime: "+dbtime
	print "dbfuel: "+dbfuel
	try:
            cur =  connection.cursor()
            sql = "INSERT INTO `obdPi` (`dbtime`,`dbrpm`,`dbmph`,`dbthrottle`,`dbload`,`dbfuel`) VALUES (%s,%s,%s,%s,%s,%s)"
            cur.execute(sql, (dbtime,dbrpm,dbmph,dbthrottle,dbload,dbfuel))
	    cur.connection.commit()
				
	finally:
	    cur.close()
	    connection.close()
				
	#Funcao para tratar os dados lidos do veiculo. Essa funcao recebe uma string e atribui cada valor a sua respectiva variavel.	
    def handle_data(self,log_string,dbtime,dbrpm,dbmph,dbthrottle,dbload,dbfuel):
	print "Data: " + log_string
	#Divide a string em um Array
	splitData = log_string.split(",")	
			
	#Sequencia de IFs para atribuir o valor a cada variavel antes de salvar no Banco	
	for index in splitData:
		print "Inside for ForLoop" + index
		if(dbtime is None):
	 		dbtime = index;
			#print "dbtime: "+dbtime
		elif(dbrpm is None):
			dbrpm = index;
			#print "dbrpm: "+dbrpm
		elif(dbmph is None):
			dbmph = index;
			#print "dbmph: "+dbmph
		elif(dbthrottle is None):
			dbthrottle = index;
			#print "dbthrottle: "+dbthrottle
		elif(dbload is None):
			dbload = index;
			#print "dbload: "+dbload
		elif(dbfuel is None):
			dbfuel = index;
			#print "dbfuel: "+dbfuel
	
	#Chama a funcao que persiste os dados.
	self.persist_data(dbtime,dbrpm,dbmph,dbthrottle,dbload,dbfuel)

            
    def calculate_gear(self, rpm, speed):
        if speed == "" or speed == 0:
            return 0
        if rpm == "" or rpm == 0:
            return 0

        rps = rpm/60
        mps = (speed*1.609*1000)/3600
        
        primary_gear = 85/46 #street triple
        final_drive  = 47/16
        
        tyre_circumference = 1.978 #meters

        current_gear_ratio = (rps*tyre_circumference)/(mps*primary_gear*final_drive)
        
        #print current_gear_ratio
        gear = min((abs(current_gear_ratio - i), i) for i in self.gear_ratios)[1] 
        return gear
        
username = getpass.getuser()  
logitems = ["rpm", "speed", "throttle_pos", "load", "fuel_status"]
o = OBD_Recorder('/home/pi/ftp/files/pyobd-pi/log/', logitems)
o.connect()

if not o.is_connected():
    print "Not connected"
o.record_data()
