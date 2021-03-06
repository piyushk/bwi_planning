#! /usr/bin/env python

import os
import subprocess
import sys

#import roslib; roslib.load_manifest('segbot_logical_translator_gui')
#import rospy

# Brings in the SimpleActionClient
#import actionlib

#import segbot_logical_translator_gui.msg



domainFile = sys.argv[1]
queryFile = sys.argv[3]
initialFile = sys.argv[2]

action = ["sense", "goto","gothrough","callforopen","approach"]
fluent = ["at", "open", "visited","beside"]

def GeneratePlan():
	plan = []
	states = []


	for i in range(20):
		inputFile = open("result","w")
		retcode = subprocess.call("clingo -c n="+str(i)+" "+domainFile+" "+initialFile+" "+queryFile, shell = True, stdout=inputFile)
		inputFile.close()

		inputFile = open("result","r")
		if inputFile.readline()=="UNSATISFIABLE\n":
#		print "goal not achieved at "+str(i)+" steps incremented..."
			continue
		else:
			print "goal achieved at "+str(i)+" steps!\n"
			for line in inputFile:
				words = line.split()
				for w in words:
					if w.find("(")!=-1:
						a1 = w[:w.find("(")]
						a2 = w[w.find("(")+1:w.rfind(")")]
						a3 = a2[:a2.rfind(",")]
						t1 = a2[a2.rfind(",")+1:]
						if w[:w.find("(")] in action:
							plan.append((t1,[a1]+a3.split(",")))
						if w[:w.find("(")] in fluent:
							states.append((t1,[a1]+a3.split(",")))
			plan = sorted(plan, key=lambda tup: tup[0])
			states = sorted(states, key=lambda tup: tup[0])
		inputFile.close()
#		print (i,plan,states)
		return (i,plan,states)

def PlannerClient():
	client = actionlib.SimpleActionClient('segbot_logical_translator_gui', segbot_logical_translator_gui.msg.ClingoInterfaceAction)
    	client.wait_for_server()

#initial state sensing:

	command = segbot_logical_translator_gui.msg.ClingoFluent("noop",[])
	print "action:noop"
	goal = segbot_logical_translator_gui.msg.ClingoInterfaceGoal(command)
	client.send_goal(goal)
	client.wait_for_result()
	result = client.get_result()

	print "Initial state sensed:"
	print result
	
	inputFile = open(sys.argv[2],"w")
	for fluent in result.observable_fluents:
		op = fluent.op
		arg = fluent.args
		curstate = (str(0),[op]+arg)
		s="("
		for i in range(1,len(curstate[1])):
			s = s + curstate[1][i]+","
			s = s+"0).\n"
			newinit = curstate[1][0]+s
		inputFile.write(newinit)
	inputFile.close()

	result = GeneratePlan()
	SendoutPlan(result,client)

def SendoutPlan(result,client):
	step = result[0]
	plan = result[1]
	state = result[2]

    	for i in range(step):
		print "send "+ str(i)+" action."
 		command = segbot_logical_translator_gui.msg.ClingoFluent(plan[i][1][0], [plan[i][1][1]])
		print "action:", plan[i][1][0], plan[i][1][1]
 		goal = segbot_logical_translator_gui.msg.ClingoInterfaceGoal(command)
		client.send_goal(goal)
		client.wait_for_result()
		result= client.get_result()
		needreplan = 0
		for fluent in result.observable_fluents:
			op = fluent.op
			arg = fluent.args
			curstate = (str(i+1),[op]+arg)
			
			if curstate in state:
				print "observation as expected: ", curstate
			else:
				print "unexpected observation: ", curstate
				needreplan = 1
				break
		if needreplan == 1:
			#generate a new initial state and calling for replan
			inputFile = open(sys.argv[2],"w")
			for fluent in result.observable_fluents:
				op = fluent.op
				arg = fluent.args
				curstate = (str(i+1),[op]+arg)
				s="("
				for i in range(1,len(curstate[1])): #arguments from second elem in list
					s = s + curstate[1][i]+","
				s = s+"0).\n"
				newinit = curstate[1][0]+s
				inputFile.write(newinit)
	#		s="("
	#		for tuple in state:
	#			if tuple[0]==str(i):
	#				print tuple
	#				for i in range(1,len(tuple[1])):
	#					s = s + tuple[1][i]+","
	#					s = s+"0).\n"
	#				newinit = tuple[1][0]+s
	#				print newinit
			#		inputFile.write(newinit)

			inputFile.close()
			newresult = GeneratePlan()
			SendoutPlan(newresult,client)
			break


if __name__ == '__main__':
	print GeneratePlan()
  #  try:
        # Initializes a rospy node so that the SimpleActionClient can
        # publish and subscribe over ROS.
  #      rospy.init_node('asp_planner_client_py')
	
  
  #      PlannerClient()
      #  print "Result:", result
  #  except rospy.ROSInterruptException:
  #      print "program interrupted before completion"


