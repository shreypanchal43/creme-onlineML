from __future__ import absolute_import
from __future__ import print_function

import os
import sys
import optparse
import random
import operator
import serial
import time
import numpy as np
import pandas as pd
import creme
from creme import metrics
import pickle
import dill


# we need to import python modules from the $SUMO_HOME/tools directory
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

from sumolib import checkBinary  # noqa
import traci  # noqa

def generate_routefile():
	random.seed(42)  # make tests reproducible
	N = 3600  # number of time steps
	# demand per second from different directions
	pWE = 1. / 20
	pEW = 1. / 15 
	pNS = 1. / 30
	pSN = 1. / 25
	with open("cross.rou.xml", "w") as routes:
		print("""<routes>
		<vType id="typeWE" accel="0.8" decel="4.5" sigma="0.5" length="5" minGap="3" maxSpeed="25" \
		guiShape="passenger"/>
		<vType id="typeNS" accel="0.8" decel="4.5" sigma="0.5" length="5" minGap="3" maxSpeed="25" guiShape="passenger"/>
		<route id="right" edges="51o 1i 2o 52i" />
		<route id="left" edges="52o 2i 1o 51i" />
		<route id="up" edges="53o 3i 4o 54i" />
		<route id="down" edges="54o 4i 3o 53i" />""", file=routes)
		vehNr = 0
		for i in range(N):
			if random.uniform(0, 1) < pWE:
				print('    <vehicle id="right_%i" type="typeWE" route="right" depart="%i" />' % (vehNr, i), file=routes)
				vehNr += 1
			if random.uniform(0, 1) < pEW:
				print('    <vehicle id="left_%i" type="typeWE" route="left" depart="%i" />' % (
					vehNr, i), file=routes)
				vehNr += 1
			if random.uniform(0, 1) < pNS:
				print('    <vehicle id="down_%i" type="typeNS" route="down" depart="%i" color="1,0,0"/>' % (
					vehNr, i), file=routes)
				vehNr += 1
			if random.uniform(0, 1) < pSN:
				print('    <vehicle id="up_%i" type="typeNS" route="up" depart="%i" color="1,0,0"/>' % (
					vehNr, i), file=routes)
				vehNr += 1				
		print("</routes>", file=routes)




arduino = serial.Serial(port='COM4', baudrate=9600, timeout=.1)
def write_read(x):
    arduino.write(bytes(x, 'utf-8'))
    time.sleep(0.05)
    data = arduino.readline()
    return data

def get_vehicle_numbers(lane):
	nu = 0
	for k in traci.lane.getLastStepVehicleIDs(lane):
		if traci.vehicle.getLanePosition(k) > 450:
			nu += 1
	return nu

def phaseDuration(junction, phase_time, phase_state):
    traci.trafficlight.setRedYellowGreenState(junction, phase_state)
    traci.trafficlight.setPhaseDuration(junction, phase_time)

def get_model():
	with open('model1_pickle.pkl', 'rb') as f:
		model1 = dill.load(f)
	return model1

def run(model1):
	"""execute the TraCI control loop"""
	step = 0
	lt=0
	z=0
	flag=0

	tls_data = [
		['yrrr', 'Grrr'],
		['ryrr', 'rGrr'],
		['rryr', 'rrGr'],
		['rrry', 'rrrG']
	] 
	
	print("simulation started ..............")
	traci.trafficlight.setPhase("0", 6)
	while traci.simulation.getMinExpectedNumber() > 0:
		traci.simulationStep()
		#sim.work()

		#For normal algorithm without model
		#For getting number of vehicle/lane and find maximum
		L1 = int(get_vehicle_numbers("1i_0"))
		L2 = int(get_vehicle_numbers("2i_0"))
		L3 = int(get_vehicle_numbers("3i_0"))
		L4 = int(get_vehicle_numbers("4i_0"))

		total_l = L1 + L2 + L3 + L4

		x = [L1, L2, L3 ,L4]
		x = np.asarray(x).astype('float32')
		data_dict2= {
			'L1':L1,
			'L2':L2,
			'L3':L3,
			'L4':L4,
		}
		
		data_dict = {
			"1i_0":L1,
			"2i_0":L2,
			"3i_0":L3,
			"4i_0":L4,
		}

		lm = max(data_dict.items(), key=operator.itemgetter(1))[0]
		lm_val = max(data_dict.items(), key=operator.itemgetter(1))[1]
		#print(lm_val)

		if lm == '1i_0':
			i = 3
		elif lm == '2i_0':
			i = 1
		elif lm == '3i_0':
			i = 2
		elif lm == '4i_0':
			i = 0

		met1 = metrics.Accuracy()
		met2 = metrics.Accuracy()

		if flag == 0:
			print("in if")
			k_pred = model1.predict_one(data_dict2)
			print(k_pred)

			if k_pred != None:
				yellow_select = tls_data[ypred][0]
				green_select = tls_data[ypred][1]
				print(yellow_select, green_select)

				phaseDuration(junction="0", phase_state=yellow_select, phase_time=6)
				phaseDuration(junction="0", phase_state=green_select, phase_time=30)
				flag =  30
			
		else:
			flag -= 1
			
		#For ARDUINO :::
		ph = str(traci.trafficlight.getPhase("0"))
		value = write_read(ph)
		step += 1
	traci.close()
	sys.stdout.flush()


def get_options():
    optParser = optparse.OptionParser()
    optParser.add_option("--nogui", action="store_true",
                         default=False, help="run the commandline version of sumo")
    options, args = optParser.parse_args()
    return options


def save_model( model2):
	# with open('model1_pickle.pkl', 'wb') as f:
	# 	dill.dump(model1, f)

	with open('model2_pickle.pkl', 'wb') as f:
		dill.dump(model2, f)


# this is the main entry point of this script
if __name__ == "__main__":
    options = get_options()
    # this script has been called from the command line. It will start sumo as a
    # server, then connect and run
    if options.nogui:
        sumoBinary = checkBinary('sumo')
    else:
        sumoBinary = checkBinary('sumo-gui')

    model1 = get_model()
    generate_routefile()
    traci.start([sumoBinary, "-c", "cross.sumocfg", "--tripinfo-output", "tripinfo.xml"])
    run(model1)


