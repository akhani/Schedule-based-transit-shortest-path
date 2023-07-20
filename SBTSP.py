### Schedule-based transit shortest path algorithm ###
################################################################################################
''' Copyright (C) 2013 by Alireza Khani
Released under the GNU General Public License, version 2.
-------------------------------------------------------
The code is entirely and originally written by Alireza Khani
Contact: akhani@umn.edu or akhani.phd@gmail.com
-------------------------------------------------------
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 2 of the License, or
(at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>. '''
################################################################################################
################################################################################################
################################################################################################

import math, time, heapq, sys
from datetime import datetime as dt 
inputDataLocation = "examples/toy network (Tong and Richardson 1988)/"
inputDataLocation = "examples/IowaCity/iowacityGTFS20220822_model/"
#inputDataLocation = "examples/TwinCities/"

################################################################################################
class Zone:
    def __init__(self, _tmpIn):
        self.lat = float(_tmpIn[1])
        self.long = float(_tmpIn[2])
        #self.nodes = []
        self.accessNode=''
        self.egressNode=''
        self.accessibleStops = []
class Stop:
    def __init__(self, _tmpIn):
        self.lat = float(_tmpIn[3])
        self.long = float(_tmpIn[4])
        self.nodes = []
class Trip:
    def __init__(self, _tmpIn):
        self.route = _tmpIn[1]
        self.type = _tmpIn[2]
        self.capacity = int(_tmpIn[3])
        self.nodes = []
        self.links = []
class Node:
    def __init__(self, _tmpIn):
        self.trip = _tmpIn[0]
        self.seq = int(_tmpIn[4])
        self.stop = _tmpIn[3]
        if _tmpIn[0]=="access" or _tmpIn[0]=="egress":
            self.meanTime = _tmpIn[2]
        else:
            self.meanTime = (int(_tmpIn[2])//10000)*60.0 + int(_tmpIn[2])%10000//100 + (int(_tmpIn[2])%100)/60.0
        self.last = 0
        self.outLinks = []
        self.inLinks = []
        self.labels = (999999.0,999999.0) #time, cost
        self.preds = ("","")
class Link:
    def __init__(self, _from, _to, _by, _time):
        self.fromNode = _from
        self.toNode = _to
        self.trip = _by
        self.time = _time
        if _by<"999999999":
            self.capacity = 25
        else:
            self.capacity = 999999
        self.passengers = []
class Passenger:
    def __init__(self, _tmpIn):
        self.origin = _tmpIn[1]
        self.destination = _tmpIn[2]
        self.direction = _tmpIn[5]
        self.PDT = float(_tmpIn[6])
        self.path = []
################################################################################################

def readParameters():
    try:
        inFile = open(inputDataLocation+"ft_input_parameters.dat", "r")
    except:
        print ("File ft_input_parameters.dat does not exist or is corrupted. The program will terminate.")
        time.sleep(1)
        sys.exit()
        
    tmpParameters = [] 
    tmpIn = inFile.readline()
    while (1):
        tmpIn = inFile.readline()
        if tmpIn == "": break
        tmpParameters.append(float(tmpIn.split()[0]))
    inFile.close()
    return tmpParameters

def readRouteChoice():
    try:
        inFile = open(inputDataLocation+"ft_input_routeChoice.dat", "r")
    except:
        print ("File ft_input_routeChoice.dat does not exist or is corrupted. The program will terminate.")
        time.sleep(1)
        sys.exit()
    tmpWeights = [] 
    tmpIn = inFile.readline()
    while (1):
        tmpIn = inFile.readline()
        if tmpIn == "": break
        tmpWeights.append(float(tmpIn.split()[0]))
    inFile.close()
    return tmpWeights

def readZones():
    try:
        inFile = open(inputDataLocation+"ft_input_zones.dat")
    except:
        print ("File ft_input_zones.dat does not exist or is corrupted. The program will terminate.")
        time.sleep(1)
        sys.exit()

    tmpIn = inFile.readline().strip().split("\t")
    for x in inFile:
        tmpIn = x.strip().split("\t")
        zoneId = tmpIn[0]
        zoneSet[zoneId] = Zone(tmpIn)
    inFile.close()
    print (len(zoneSet), "zones")
def readStops():
    try:
        inFile = open(inputDataLocation+"ft_input_stops.dat")
    except:
        print ("File ft_input_stops.dat does not exist or is corrupted. The program will terminate.")
        sys.exit()

    tmpIn = inFile.readline().strip().split("\t")
    for x in inFile:
        tmpIn = x.strip().split("\t")
        stopSet[tmpIn[0]] = Stop(tmpIn)
    inFile.close()
    print (len(stopSet), "stops")
def readTrips():
    try:
        inFile = open(inputDataLocation+"ft_input_trips.dat")
    except:
        print ("File ft_input_trips.dat does not exist or is corrupted. The program will terminate.")
        sys.exit()

    tmpIn = inFile.readline().strip().split("\t")
    for x in inFile:
        tmpIn = x.strip().split("\t")
        tripSet[tmpIn[0]] = Trip(tmpIn)
    inFile.close()
    print (len(tripSet), "trips")
def readSchedule():
    try:
        inFile = open(inputDataLocation+"ft_input_stopTimes.dat")
    except:
        print ("File ft_input_stopTimes.dat does not exist or is corrupted. The program will terminate.")
        sys.exit()
    
    tmpIn = inFile.readline().strip().split("\t")
    prevNodeId = ""
    for x in inFile:
        tmpIn = x.strip().split("\t")
        tripId = tmpIn[0]
        stopId = tmpIn[3]
        seq = tmpIn[4]
        nodeId = tripId+","+seq+","+stopId
        nodeSet[nodeId] = Node(tmpIn)
        stopSet[stopId].nodes.append(nodeId)
        if int(seq)==1 and prevNodeId!="":
            nodeSet[prevNodeId].last=1
        if int(seq)>1:
            linkId = tripId+","+str(int(seq)-1)
            linkSet[linkId] = Link(prevNodeId, nodeId, tripId, 0)
            nodeSet[prevNodeId].outLinks.append(linkId)
            nodeSet[nodeId].inLinks.append(linkId)
        prevNodeId = nodeId
    inFile.close()
    print (len(nodeSet), "nodes")
    print (len(linkSet), "transit links")
    # Create waiting transfer links
    for s in stopSet:
        for n1 in stopSet[s].nodes:
            for n2 in stopSet[s].nodes:
                if n1!=n2 and nodeSet[n1].seq!=1 and nodeSet[n2].last!=1 and nodeSet[n1].stop==nodeSet[n2].stop and tripSet[nodeSet[n1].trip].route!=tripSet[nodeSet[n2].trip].route:
                    if nodeSet[n2].meanTime>=nodeSet[n1].meanTime and nodeSet[n2].meanTime<nodeSet[n1].meanTime+MODEL_SETTINGS['TRANSFER_TIME_WINDOW']:   ### the constant value determines an acceptable time window
                        linkId = "transfer"+","+str(len(linkSet)+1)
                        linkSet[linkId] = Link(n1, n2, "waitingtransfer", 0)
                        nodeSet[n1].outLinks.append(linkId)
                        nodeSet[n2].inLinks.append(linkId)
                        #print i, nodeSet[n1].stop, nodeSet[n1].trip, nodeSet[n2].trip
    print (len(linkSet), "transit+waitingtransfer links")
def readTransferLinks():
    try:
        inFile = open(inputDataLocation+"ft_input_transfers.dat")
    except:
        print ("File ft_input_transfers.dat does not exist or is corrupted. The program will terminate.")
        sys.exit()
        
    if MODEL_SETTINGS['WALKING_TRANSFERS?'] == 1:
        tmpIn = inFile.readline().strip().split("\t")
        for x in inFile:
            tmpIn = x.strip().split("\t")
            #print len(tmpIn), len(linkSet)
            if float(tmpIn[2]) <= MODEL_SETTINGS['TRANSFER_WALKING_THRESHOLD']:
                fromNodes = stopSet[tmpIn[0]].nodes
                toNodes = stopSet[tmpIn[1]].nodes
                # Create walking transfer links
                for n1 in fromNodes:
                    for n2 in toNodes:
                        if nodeSet[n1].seq!=1 and nodeSet[n2].last!=1 and tripSet[nodeSet[n1].trip].route!=tripSet[nodeSet[n2].trip].route:
                            if nodeSet[n2].meanTime >= nodeSet[n1].meanTime+float(tmpIn[3]) and nodeSet[n2].meanTime <= nodeSet[n1].meanTime+float(tmpIn[3])+MODEL_SETTINGS['TRANSFER_TIME_WINDOW'] :    ### the constant value determines an acceptable time window
                                linkId = "transfer"+","+str(len(linkSet)+1)
                                if linkId in linkSet:
                                    print ("ERROR in reading transfers")
                                linkSet[linkId] = Link(n1, n2, "walkingtransfer", float(tmpIn[3]))
                                nodeSet[n1].outLinks.append(linkId)
                                nodeSet[n2].inLinks.append(linkId)
        inFile.close()
        print (len(linkSet), "transit+waitingtransfer+walkingtransfer links")
    else:
        print (" * walkingtransfer links are not added. If they should be added, change the parameter in ft_input_parameters.dat")

def readAccessLinks():
    try:
        inFile = open(inputDataLocation+"ft_input_accessLinks.dat")
    except:
        print ("File ft_input_accessLinks.dat does not exist or is corrupted. The program will terminate.")
        sys.exit()

    tmpIn = inFile.readline().strip().split("\t")
    for x in inFile:
        tmpIn = x.strip().split("\t")
        zoneId = tmpIn[0]
        stopId = tmpIn[1]
        tmpNodes = stopSet[stopId].nodes
        zoneSet[zoneId].accessibleStops.append([stopId, float(tmpIn[2]), float(tmpIn[3])]) # distance (miles) and time (minutes)
        
        nodeId = "access" + "," + tmpIn[0]
        if not(nodeId in nodeSet):
            nodeSet[nodeId] = Node(["access", -1, -1, zoneId, 0])
        #zoneSet[zoneId].nodes.append(nodeId)
        zoneSet[zoneId].accessNode=nodeId
#        for n in tmpNodes:
#            if nodeSet[n].last!=1:
#                linkId = "access"+","+str(len(linkSet)+1)
#                if linkId in linkSet:
#                    print ("ERROR in reading access links")
#                linkSet[linkId] = Link(nodeId, n, "access", float(tmpIn[3]))
#                nodeSet[nodeId].outLinks.append(linkId)
#                nodeSet[n].inLinks.append(linkId)
        nodeId = "egress" + "," + tmpIn[0]
        nodeSet[nodeId] = Node(["egress", -1, -1, zoneId, 0])
        #zoneSet[zoneId].nodes.append(nodeId)
        zoneSet[zoneId].egressNode=nodeId
#        for n in tmpNodes:
#            if nodeSet[n].seq!=1:
#                linkId = "egress"+","+str(len(linkSet)+1)
#                if linkId in linkSet:
#                    print ("ERROR in reading access links")
#                linkSet[linkId] = Link(n, nodeId, "egress", float(tmpIn[3]))
#                nodeSet[n].outLinks.append(linkId)
#                nodeSet[nodeId].inLinks.append(linkId)
    inFile.close()
    print (len(linkSet), "transit+waitingtransfer+walkingtransfer+access+egress links")

def readDemand():
    try:
        inFile = open(inputDataLocation+"ft_input_demand.dat")
    except:
        print ("File ft_input_demand.dat does not exist or is corrupted. The program will terminate.")
        sys.exit()

    tmpIn = inFile.readline().strip().split("\t")
    for x in inFile:
        tmpIn = x.strip().split("\t")
        passengerId = tmpIn[0]
        passengerSet[passengerId] = Passenger(tmpIn)
    inFile.close()
    print (len(passengerSet), "passengers")
################################################################################################
def sortConnectors():
    for node in nodeSet:
        if len(nodeSet[node].inLinks)>1:
            nodeSet[node].inLinks.sort(key=lambda x: nodeSet[linkSet[x].fromNode].meanTime+linkSet[x].time)
################################################################################################
def findShortestPath(orig, PDT, pathType):
    for n in nodeSet:
        nodeSet[n].labels = (999999, 999999, 1.0)
        nodeSet[n].preds = ("", "")
    #if zoneSet[orig].nodes==[]:
    #if zoneSet[orig].accessNode=='':
    #    print('Origin', orig, 'does not have an access node')
    #    return [-1, []]

    #accessNode = zoneSet[orig].nodes[0]
    accessNode = zoneSet[orig].accessNode
    nodeSet[accessNode].labels = (PDT,0,1)
    #SE = [accessNode]
    SE = [((nodeSet[accessNode].labels[2], accessNode))]
    it=0
    iLabel = 0
    while len(SE)>0:
        #currentNode = SE[0]
        #currentLabels = nodeSet[currentNode].labels
        #SE.remove(currentNode)
        currentNode = heapq.heappop(SE)[1]
        currentLabels = nodeSet[currentNode].labels
        currentPreds = nodeSet[currentNode].preds
        it = it+1
        for link in nodeSet[currentNode].outLinks:
            newNode = linkSet[link].toNode
            newPreds = [currentNode, link]
            existingLabels = nodeSet[newNode].labels
            newLabels = []
            ### Calculate new labels
            if linkSet[link].trip=="access":
                if PDT+linkSet[link].time<=nodeSet[newNode].meanTime and PDT+linkSet[link].time+30>nodeSet[newNode].meanTime:
                    newLabels.append(round(nodeSet[newNode].meanTime,3))
                    newLabels.append(round(ROUTE_CHOICE['WALKING_TIME']*linkSet[link].time+ROUTE_CHOICE['WAITING_TIME']*(nodeSet[newNode].meanTime-linkSet[link].time-PDT),3))
                else:
                    continue
            elif linkSet[link].trip=="egress" and linkSet[currentPreds[1]].trip not in ['access','waitingtransfer','walkingtransfer']:
                newLabels.append(round(currentLabels[0]+linkSet[link].time,3))
                newLabels.append(round(currentLabels[1]+ROUTE_CHOICE['WALKING_TIME']*linkSet[link].time,3))
            elif linkSet[link].trip=="waitingtransfer" and linkSet[currentPreds[1]].trip not in ['access','waitingtransfer','walkingtransfer']:
                newLabels.append(round(nodeSet[newNode].meanTime,3))
                newLabels.append(round(currentLabels[1]+ROUTE_CHOICE['TRANSFER_PENALTY']+ROUTE_CHOICE['WAITING_TIME']*(nodeSet[newNode].meanTime-nodeSet[currentNode].meanTime),3))
            elif linkSet[link].trip=="walkingtransfer" and linkSet[currentPreds[1]].trip not in ['access','waitingtransfer','walkingtransfer']:
                newLabels.append(round(nodeSet[newNode].meanTime,3))
                newLabels.append(round(currentLabels[1]+ROUTE_CHOICE['TRANSFER_PENALTY']+ROUTE_CHOICE['WALKING_TIME']*linkSet[link].time+ROUTE_CHOICE['WAITING_TIME']*(nodeSet[newNode].meanTime-nodeSet[currentNode].meanTime-linkSet[link].time),3))
            elif linkSet[link].trip not in ['access', 'waitingtransfer', 'walkingtransfer', 'egress']:# and linkSet[currentPreds[1]].trip in ['egress','waitingtransfer','walkingtransfer']:
                newLabels.append(round(nodeSet[newNode].meanTime,3))
                newLabels.append(round(currentLabels[1]+ROUTE_CHOICE['IN_VEHICLE_TIME']*(nodeSet[newNode].meanTime-nodeSet[currentNode].meanTime),3))
            else:                
                continue
            ### Update the node labels
            if pathType=="fastest" and newLabels[0]<existingLabels[0]:
                nodeSet[newNode].labels = newLabels
                nodeSet[newNode].preds = newPreds
                #SE.append(newNode)
                heapq.heappush(SE, (newLabels[0], newNode))
            elif pathType=="optimal" and newLabels[1]<existingLabels[1]:
                nodeSet[newNode].labels = newLabels
                nodeSet[newNode].preds = newPreds
                #SE.append(newNode)
                heapq.heappush(SE, (newLabels[1], newNode))
            elif pathType=="reliable": ## Most likely not working and needs to be investigated
                if newLabels[2]>existingLabels[2] or (newLabels[2]==existingLabels[2] and newLabels[1]<existingLabels[1]):
                    nodeSet[newNode].labels = newLabels
                    nodeSet[newNode].preds = newPreds
                    #SE.append(newNode)
                    heapq.heappush(SE, (newLabels[2], newNode))
    return [it, iLabel]
def getShortetstPath(dest):
    #try:
    #    currentNode = zoneSet[dest].nodes[1]
    #except IndexError:
    #    print "No transit stops connected to zone", dest
    #    return []
    currentNode = zoneSet[dest].egressNode
    if nodeSet[currentNode].labels[1]>=999999:
        return []
    path = []
    while currentNode!="":
        newNode = nodeSet[currentNode].preds[0]
        newLink = nodeSet[currentNode].preds[1]
        if newNode!="":
            path = [newLink] + path
        currentNode = newNode
    return path
################################################################################################
def printLinkFlows():
    outFile = open(inputDataLocation+"ft_output_linkFlows.dat", "w")
    tmpOut = "route\ttrip\tsequence\tfrom\tto\tflow"
    outFile.write(tmpOut+"\n")
    for link in linkSet:
        if len(linkSet[link].passengers)>=0:
            if link.split(",")[0]<"999999999":
                tmpOut = tripSet[linkSet[link].trip].route+"\t"+linkSet[link].trip+"\t"+link.split(",")[1]+"\t"+nodeSet[linkSet[link].fromNode].stop+"\t"+nodeSet[linkSet[link].toNode].stop+"\t"+str(len(linkSet[link].passengers))
            elif link.split(",")[0]=="transfer":
                tmpOut = link.split(",")[0]+"\t"+tripSet[nodeSet[linkSet[link].fromNode].trip].route+"\t"+tripSet[nodeSet[linkSet[link].toNode].trip].route+"\t"+nodeSet[linkSet[link].fromNode].stop+"\t"+nodeSet[linkSet[link].toNode].stop+"\t"+str(len(linkSet[link].passengers))
            else:
                tmpOut = link.split(",")[0]+"\t"+linkSet[link].fromNode[0]+"\t"+linkSet[link].toNode[0]+"\t"+nodeSet[linkSet[link].fromNode].stop+"\t"+nodeSet[linkSet[link].toNode].stop+"\t"+str(len(linkSet[link].passengers))
            outFile.write(tmpOut+"\n")
    outFile.close()
def printPaths():
    outFile = open(inputDataLocation+"ft_output_paths.dat", "w")
    tmpOut = "passenger\torigin\tdestination\tPDT\tpath"
    outFile.write(tmpOut+"\n")
    for passenger in passengerSet:
        orig = passengerSet[passenger].origin
        dest = passengerSet[passenger].destination
        PDT = passengerSet[passenger].PDT
        path = passengerSet[passenger].path
        tmpOut = passenger+"\t"+orig+"\t"+dest+"\t"+str(PDT)+"\t"+str(path)
        outFile.write(tmpOut+"\n")
    outFile.close()
def printUnlinkedTrips():
    outFile = open(inputDataLocation+"ft_output_unlinkedTrips.dat", "w")
    tmpOut = "passenger\ttripSequence\trouteID\ttripID\tboardingStopID\tboardingStopLat\tboardingStopLon\tboardingTime\talightingStopID\talightingStopLat\talightingStopLon\talightingTime\n"
    outFile.write(tmpOut)
    for passenger in passengerSet:
        tripID = ''
        seq = 1
        for p in passengerSet[passenger].path:
            if p.split(',')[0] == 'access': ## access/egress links don't exist in the network!
                continue
            elif p.split(',')[0] == 'egress': ## access/egress links don't exist in the network!
                outFile.write(tmpOut+'\n')  ## this new line prints the aligting information 
                continue 
            elif p.split(',')[0] == 'transfer': ## access/egress links don't exist in the network!
                outFile.write(tmpOut+'\n')  ## this new line prints the aligting information 
                seq += 1
                continue
            else:
                if linkSet[p].trip != tripID:
                    tripID = linkSet[p].trip
                    routeID = tripSet[tripID].route
                    stopNode = linkSet[p].fromNode
                    stopID = nodeSet[stopNode].stop
                    stopLat = round(stopSet[stopID].lat,6)
                    stopLong = round(stopSet[stopID].long,6)
                    boardTime = round(nodeSet[stopNode].meanTime,1)
                    tmpOut = str(passenger)+'\t'+str(seq)+'\t'+str(routeID)+'\t'+str(tripID)+'\t'+str(stopID)+'\t'+str(stopLat)+'\t'+str(stopLong)+'\t'+str(boardTime)
                    outFile.write(tmpOut)
                    stopNode = linkSet[p].toNode
                    stopID = nodeSet[stopNode].stop
                    stopLat = round(stopSet[stopID].lat,6)
                    stopLong = round(stopSet[stopID].long,6)
                    alightTime = round(nodeSet[stopNode].meanTime + linkSet[p].time,1)
                    tmpOut = '\t'+str(stopID)+'\t'+str(stopLat)+'\t'+str(stopLong)+'\t'+str(alightTime)
                else:
                    stopNode = linkSet[p].toNode
                    stopID = nodeSet[stopNode].stop
                    stopLat = round(stopSet[stopID].lat,6)
                    stopLong = round(stopSet[stopID].long,6)
                    alightTime = round(nodeSet[stopNode].meanTime + linkSet[p].time,1)
                    tmpOut = '\t'+str(stopID)+'\t'+str(stopLat)+'\t'+str(stopLong)+'\t'+str(alightTime)
    outFile.close()

def printPassengerRoutes():
    outFile = open(inputDataLocation+'ft_output_passengerRoutes.dat', 'w')
    tmpOut = "passenger\torigin\tdestination\troutes"
    outFile.write(tmpOut+'\n')
    for passenger in passengerSet:
        routes = []
        orig = passengerSet[passenger].origin
        dest = passengerSet[passenger].destination
        path = passengerSet[passenger].path
        for segment in path:
            if segment[0] != 'a' and segment[0] != 'e':
                if linkSet[segment].trip not in ['access', 'waitingtransfer', 'walkingtransfer', 'egress']:
                    tripID = linkSet[segment].trip
                    routeID = tripSet[tripID].route
                    routes.append(routeID)
        tmpOut = str(passenger)+'\t'+str(orig)+'\t'+str(dest)
        routes = set(routes)
        for r in routes:
            tmpOut = tmpOut+'\t'+str(r)

        outFile.write(tmpOut+'\n')
    outFile.close()
################################################################################################


def assignPassengers(_pathType):
    counter = 0
    assigned = 0
    startTime = time.time()
    
    #print ("Assignment starting with:", sum([len(nodeSet[x].outLinks) for x in nodeSet]), sum([len(nodeSet[x].inLinks) for x in nodeSet]))

    i=0
    for passenger in passengerSet:
        i=i+1
        orig = passengerSet[passenger].origin
        dest = passengerSet[passenger].destination
        PDT = passengerSet[passenger].PDT
        
        ##### Find available access points for passenger #####
        tmpLinksA = []
        tmpNodesA = []
        nodeId = "access" + "," + orig
        #if not(nodeId in nodeSet):
        #    nodeSet[nodeId] = Node(["access", -1, -1, orig, 0])
        #    #zoneSet[orig].nodes.append(nodeId)
        #    zoneSet[orig].accessNode=nodeId
        if zoneSet[orig].accessibleStops == []:
            logFile.write("\t * Passenger %4s does not have an accessible stop from origin zone %4s\n" %(passenger, orig))
            #continue
        else:
            for stp in zoneSet[orig].accessibleStops:
                if stp[1] <= MODEL_SETTINGS['ACCESS_WALKING_THRESHOLD']: ## access walking distance treshold
                    tmpNodes = stopSet[stp[0]].nodes
                    for n in tmpNodes:
                        tmpWalkTime = stp[2]
                        if nodeSet[n].meanTime > PDT + tmpWalkTime and nodeSet[n].meanTime < PDT + tmpWalkTime + MODEL_SETTINGS['ACCESS_TIME_WINDOW']:
                            if nodeSet[n].last!=1:
                                linkId = "access"+","+str(len(linkSet)+1)
                                if linkId in linkSet:
                                    print ('ERROR - Access link', linkId, 'already in linkSet!')
                                else:
                                    linkSet[linkId] = Link(nodeId, n, "access", tmpWalkTime)
                                    nodeSet[nodeId].outLinks.append(linkId)
                                    nodeSet[n].inLinks.append(linkId)
                                    tmpLinksA.append(linkId)
                                    tmpNodesA.append(n)

        ##### Find available egress points for passenger #####
        tmpLinksE = []
        tmpNodesE = []
        nodeId = "egress" + "," + dest
        #if not(nodeId in nodeSet):
        #    nodeSet[nodeId] = Node(["egress", -1, -1, dest, 0])
        #    #zoneSet[dest].nodes.append(nodeId)
        #    zoneSet[dest].egressNode=nodeId
        if zoneSet[dest].accessibleStops == []:
            logFile.write("\t * Passenger %4s does not have an accessible stop from destination zone %4s\n" %(passenger, dest))
            #continue
        else:
            for stp in zoneSet[dest].accessibleStops:
                if stp[1] <= MODEL_SETTINGS['ACCESS_WALKING_THRESHOLD']: ## egress walking distance treshold
                    tmpNodes = stopSet[stp[0]].nodes
                    for n in tmpNodes:
                        tmpWalkTime = stp[2]
                        if nodeSet[n].meanTime + tmpWalkTime > PDT and nodeSet[n].meanTime < PDT + MODEL_SETTINGS['MAX_TRIP_DURATION']:# limit transit trips to 5 hours tmpWalkTime > PDT - ACCESS_TIME_WINDOW:
                            if nodeSet[n].seq!=1:
                                linkId = "egress"+","+str(len(linkSet)+1)
                                if linkId in linkSet:
                                    print ('ERROR - Egress link', linkId, 'already in linkSet!')
                                else:
                                    linkSet[linkId] = Link(n, nodeId, "egress", tmpWalkTime)
                                    nodeSet[n].outLinks.append(linkId)
                                    nodeSet[nodeId].inLinks.append(linkId)
                                    tmpLinksE.append(linkId)
                                    tmpNodesE.append(n)
        if len(tmpLinksA)>0 and len(tmpLinksE)>0:                
            sortConnectors()
            counter = counter + 1
            iter = findShortestPath(orig, PDT, _pathType)[0]
            path = getShortetstPath(dest)
            if path==[]:
                logFile.write("\t *** No path was found for passenger %4s\n" %(passenger))# , '\tverify with min stop label: ', min([nodeSet[n].labels[1] for n in tmpNodesE]))
            else:
                assigned = assigned + 1
            #if counter%10==0:
            #    print (counter,"\tout of\t",len(passengerSet), "\tpassengers;\t", iter, "\titerations\t", round(time.time()-startTime,3), "\tsecond")
            #    print passenger, orig, dest, PDT, "path:", path
            passengerSet[passenger].path = path
            for link in path:
                linkSet[link].passengers.append(passenger)
        timeCount = round(time.time()-startTime,3)
        if i%10==0:
            print ("Passengers evaluated:", i, ", with access:", counter, ", assigned", assigned, ", time elapsed:", timeCount, "seconds.")
        
        ### Remove passenger access/egress links from memory
        
        try:
            nodeSet["access" + "," + orig].outLinks = []
        except:
            1
        try:
            nodeSet["egress" + "," + dest].inLinks = []
        except:
            1
        
        for n in tmpNodesA:
            for l in nodeSet[n].inLinks:
                if l.split(",")[0] == 'access':
                    nodeSet[n].inLinks.remove(l)
        for n in tmpNodesE:
            for l in nodeSet[n].outLinks:
                if l.split(",")[0] == 'egress':
                    nodeSet[n].outLinks.remove(l)
        for link in tmpLinksA:
            del linkSet[link]
        for link in tmpLinksE:
            del linkSet[link]
        tmpLinksA = []
        tmpNodesA = []
        tmpLinksE = []
        tmpNodesE = []
        #print (len(linkSet), len(nodeSet), sum([len(nodeSet[x].outLinks) for x in nodeSet]), sum([len(nodeSet[x].inLinks) for x in nodeSet]))
        
    printLinkFlows()
    printPaths()
    printUnlinkedTrips()
    printPassengerRoutes()
################################################################################################
zoneSet = {}
stopSet = {}
tripSet = {}
nodeSet = {}
linkSet = {}
passengerSet = {}
MODEL_SETTINGS = {}
ROUTE_CHOICE = {}


logFile = open(inputDataLocation+"ft_output_log.dat", "w")
print ("------------------------------")
logFile.write("%4s - Reading the input files. \n" %(dt.fromtimestamp(time.time())) )
logFile.write("--------------------------------------------------\n")
parameters = readParameters() 
MODEL_SETTINGS['ACCESS_WALKING_THRESHOLD']      = parameters[0]
MODEL_SETTINGS['TRANSFER_WALKING_THRESHOLD']    = parameters[1]
MODEL_SETTINGS['WALKING_TRANSFERS?']            = parameters[2]
MODEL_SETTINGS['ACCESS_TIME_WINDOW']            = parameters[3]
MODEL_SETTINGS['TRANSFER_TIME_WINDOW']          = parameters[4]
MODEL_SETTINGS['MAX_TRIP_DURATION']             = parameters[5]
#print (MODEL_SETTINGS)

weights = readRouteChoice() #IVT, WT, WK, TR, schedule delay ### schedule delay can be added to relax early arrival penalty
ROUTE_CHOICE['IN_VEHICLE_TIME']     = weights[0]
ROUTE_CHOICE['WAITING_TIME']        = weights[1]
ROUTE_CHOICE['WALKING_TIME']        = weights[2]
ROUTE_CHOICE['TRANSFER_PENALTY']    = weights[3]
ROUTE_CHOICE['SCHEDULE_DELAY']      = weights[4] ##    It seems that this is not incorportaed in the algorithm although it could be that the algorithm automatically ignores schedule delay. It has to be cheched. 
#print (ROUTE_CHOICE)


readZones()
readStops()
readTrips()
readSchedule()
readTransferLinks()
readAccessLinks()
readDemand()
print ("------------------------------")
logFile.write("%4s - Starting the assignment. \n" %(dt.fromtimestamp(time.time())) )
logFile.write("--------------------------------------------------\n")
sortConnectors()
assignPassengers("optimal") ## for now, the parameter should be "optimal"
logFile.write("--------------------------------------------------\n")
logFile.write("%4s - Assignment completed. \n" %(dt.fromtimestamp(time.time())) )
logFile.write("--------------------------------------------------\n")
print ("------------------------------")
logFile.close()