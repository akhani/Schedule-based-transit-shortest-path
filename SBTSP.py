################################################################################################
### Schedule-based transit shortest path algorithm ###
################################################################################################
''' Copyright (C) 2013 by Alireza Khani
Released under the GNU General Public License, version 2.
-------------------------------------------------------
Code primarily written by Alireza Khani
Contact: akhani@umn.edu
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

import math, time, heapq
inputDataLocation = "test network (Tong and Richardson 1988)/"

################################################################################################
class Zone:
    def __init__(self, _tmpIn):
        self.lat = float(_tmpIn[1])
        self.long = float(_tmpIn[2])
        self.nodes = []
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
def readZones():
    inFile = open(inputDataLocation+"ft_input_zones.dat")
    tmpIn = inFile.readline().strip().split("\t")
    for x in inFile:
        tmpIn = x.strip().split("\t")
        zoneId = tmpIn[0]
        zoneSet[zoneId] = Zone(tmpIn)
    inFile.close()
    print len(zoneSet), "zones"
def readStops():
    inFile = open(inputDataLocation+"ft_input_stops.dat")
    tmpIn = inFile.readline().strip().split("\t")
    for x in inFile:
        tmpIn = x.strip().split("\t")
        stopSet[tmpIn[0]] = Stop(tmpIn)
    inFile.close()
    print len(stopSet), "stops"
def readTrips():
    inFile = open(inputDataLocation+"ft_input_trips.dat")
    tmpIn = inFile.readline().strip().split("\t")
    for x in inFile:
        tmpIn = x.strip().split("\t")
        tripSet[tmpIn[0]] = Trip(tmpIn)
    inFile.close()
    print len(tripSet), "trips"
def readSchedule():
    inFile = open(inputDataLocation+"ft_input_stopTimes.dat")
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
    print len(nodeSet), "nodes"
    print len(linkSet), "transit links"
    # Create waiting transfer links
    for s in stopSet:
        for n1 in stopSet[s].nodes:
            for n2 in stopSet[s].nodes:
                if n1!=n2 and nodeSet[n1].seq!=1 and nodeSet[n2].last!=1 and nodeSet[n1].stop==nodeSet[n2].stop and tripSet[nodeSet[n1].trip].route!=tripSet[nodeSet[n2].trip].route:
                    if nodeSet[n2].meanTime>=nodeSet[n1].meanTime and nodeSet[n2].meanTime<nodeSet[n1].meanTime+10:   ### the constant value determines an acceptable time window
                        linkId = "transfer"+","+str(len(linkSet)+1)
                        linkSet[linkId] = Link(n1, n2, "waitingtransfer", 0)
                        nodeSet[n1].outLinks.append(linkId)
                        nodeSet[n2].inLinks.append(linkId)
                        #print i, nodeSet[n1].stop, nodeSet[n1].trip, nodeSet[n2].trip
    print len(linkSet), "transit+waitingtransfer links"
def readTransferLinks():
    inFile = open(inputDataLocation+"ft_input_transfers.dat")
    tmpIn = inFile.readline().strip().split("\t")
    for x in inFile:
        tmpIn = x.strip().split("\t")
        #print len(tmpIn), len(linkSet)
        fromNodes = stopSet[tmpIn[0]].nodes
        toNodes = stopSet[tmpIn[1]].nodes
        # Create walking transfer links
        for n1 in fromNodes:
            for n2 in toNodes:
                if nodeSet[n1].seq!=1 and nodeSet[n2].last!=1 and tripSet[nodeSet[n1].trip].route!=tripSet[nodeSet[n2].trip].route:
                    if nodeSet[n2].meanTime>=nodeSet[n1].meanTime+float(tmpIn[3]) and nodeSet[n2].meanTime<nodeSet[n1].meanTime+float(tmpIn[3])+10:    ### the constant value determines an acceptable time window
                        linkId = "transfer"+","+str(len(linkSet)+1)
                        if linkId in linkSet:
                            print "ERROR"
                        linkSet[linkId] = Link(n1, n2, "walkingtransfer", float(tmpIn[3]))
                        nodeSet[n1].outLinks.append(linkId)
                        nodeSet[n2].inLinks.append(linkId)
    inFile.close()
    print len(linkSet), "transit+waitingtransfer+walkingtransfer links"
def readAccessLinks():
    inFile = open(inputDataLocation+"ft_input_accessLinks.dat")
    tmpIn = inFile.readline().strip().split("\t")
    for x in inFile:
        tmpIn = x.strip().split("\t")
        zoneId = tmpIn[0]
        tmpNodes = stopSet[tmpIn[1]].nodes
        nodeId = "access" + "," + tmpIn[0]
        if not(nodeId in nodeSet):
            nodeSet[nodeId] = Node(["access", -1, -1, zoneId, 0])
        zoneSet[zoneId].nodes.append(nodeId)
        for n in tmpNodes:
            if nodeSet[n].last!=1:
                linkId = "access"+","+str(len(linkSet)+1)
                if linkId in linkSet:
                    print "ERROR"
                linkSet[linkId] = Link(nodeId, n, "access", float(tmpIn[3]))
                nodeSet[nodeId].outLinks.append(linkId)
                nodeSet[n].inLinks.append(linkId)
        nodeId = "egress" + "," + tmpIn[0]
        nodeSet[nodeId] = Node(["egress", -1, -1, zoneId, 0])
        zoneSet[zoneId].nodes.append(nodeId)
        for n in tmpNodes:
            if nodeSet[n].seq!=1:
                linkId = "egress"+","+str(len(linkSet)+1)
                if linkId in linkSet:
                    print "ERROR"
                linkSet[linkId] = Link(n, nodeId, "egress", float(tmpIn[3]))
                nodeSet[n].outLinks.append(linkId)
                nodeSet[nodeId].inLinks.append(linkId)
    inFile.close()
    print len(linkSet), "transit+waitingtransfer+walkingtransfer+access+egress links"
def readDemand():
    inFile = open(inputDataLocation+"ft_input_demand.dat")
    tmpIn = inFile.readline().strip().split("\t")
    for x in inFile:
        tmpIn = x.strip().split("\t")
        passengerId = tmpIn[0]
        passengerSet[passengerId] = Passenger(tmpIn)
    inFile.close()
    print len(passengerSet), "passengers"
################################################################################################
def sortConnectors():
    for node in nodeSet:
        if len(nodeSet[node].inLinks)>1:
            nodeSet[node].inLinks.sort(key=lambda x: nodeSet[linkSet[x].fromNode].meanTime+linkSet[x].time)
################################################################################################
def findShortestPath(orig, PDT, pathType):
    for n in nodeSet:
        nodeSet[n].labels = (999999, 999999, 1.0)
        nodeSet[n].pred = ("", "")
    if zoneSet[orig].nodes==[]:
        return -1
    accessNode = zoneSet[orig].nodes[0]
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
                    newLabels.append(round(weights[2]*linkSet[link].time+weights[1]*(nodeSet[newNode].meanTime-linkSet[link].time-PDT),3))
                else:
                    continue
            elif linkSet[link].trip=="egress":
                newLabels.append(round(currentLabels[0]+linkSet[link].time,3))
                newLabels.append(round(currentLabels[1]+weights[2]*linkSet[link].time,3))
            elif linkSet[link].trip=="waitingtransfer":
                newLabels.append(round(nodeSet[newNode].meanTime,3))
                newLabels.append(round(currentLabels[1]+weights[3]+weights[1]*(nodeSet[newNode].meanTime-nodeSet[currentNode].meanTime),3))
            elif linkSet[link].trip=="walkingtransfer":
                newLabels.append(round(nodeSet[newNode].meanTime,3))
                newLabels.append(round(currentLabels[1]+weights[3]+weights[2]*linkSet[link].time+weights[1]*(nodeSet[newNode].meanTime-nodeSet[currentNode].meanTime-linkSet[link].time),3))
            else:
                newLabels.append(round(nodeSet[newNode].meanTime,3))
                newLabels.append(round(currentLabels[1]+weights[0]*(nodeSet[newNode].meanTime-nodeSet[currentNode].meanTime),3))
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
            elif pathType=="reliable":
                if newLabels[2]>existingLabels[2] or (newLabels[2]==existingLabels[2] and newLabels[1]<existingLabels[1]):
                    nodeSet[newNode].labels = newLabels
                    nodeSet[newNode].preds = newPreds
                    #SE.append(newNode)
                    heapq.heappush(SE, (newLabels[2], newNode))
    return [it, iLabel]
def getShortetstPath(dest):
    currentNode = zoneSet[dest].nodes[1]
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
    outFile = open("linkFlows.dat", "w")
    tmpOut = "route\ttrip\tsequence\tfrom\tto\tflow"
    outFile.write(tmpOut+"\n")
    for link in linkSet:
        if len(linkSet[link].passengers)>0:
            if link.split(",")[0]<"999999999":
                tmpOut = tripSet[linkSet[link].trip].route+"\t"+linkSet[link].trip+"\t"+link.split(",")[1]+"\t"+nodeSet[linkSet[link].fromNode].stop+"\t"+nodeSet[linkSet[link].toNode].stop+"\t"+str(len(linkSet[link].passengers))
            elif link.split(",")[0]=="transfer":
                tmpOut = link.split(",")[0]+"\t"+tripSet[nodeSet[linkSet[link].fromNode].trip].route+"\t"+tripSet[nodeSet[linkSet[link].toNode].trip].route+"\t"+nodeSet[linkSet[link].fromNode].stop+"\t"+nodeSet[linkSet[link].toNode].stop+"\t"+str(len(linkSet[link].passengers))
            else:
                tmpOut = link.split(",")[0]+"\t"+linkSet[link].fromNode[0]+"\t"+linkSet[link].toNode[0]+"\t"+nodeSet[linkSet[link].fromNode].stop+"\t"+nodeSet[linkSet[link].toNode].stop+"\t"+str(len(linkSet[link].passengers))
            outFile.write(tmpOut+"\n")
    outFile.close()
def printPaths():
    outFile = open("paths.dat", "w")
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
################################################################################################
def assignPassengers(_pathType):
    print
    counter = 0
    assigned = 0
    startTime = time.clock()
    for passenger in passengerSet:
        orig = passengerSet[passenger].origin
        dest = passengerSet[passenger].destination
        PDT = passengerSet[passenger].PDT
        iter = findShortestPath(orig, PDT, _pathType)[0]
        if iter==-1:
            print "No Access"
        path = getShortetstPath(dest)
        if path==[]:
            print "No Path"
        else:
            assigned = counter + 1
        counter = counter + 1
        if counter%100==0:
            print counter,"\tout of\t",len(passengerSet), "\tpassengers;\t", iter, "\titerations\t", round(time.clock()-startTime,3), "\tsecond"
            #print passenger, orig, dest, PDT, "path:", path
        passengerSet[passenger].path = path
        for link in path:
            linkSet[link].passengers.append(passenger)
    print assigned, "passengers assigned in", round(time.clock()-startTime,3), "seconds."
    printLinkFlows()
    printPaths()
################################################################################################
zoneSet = {}
stopSet = {}
tripSet = {}
nodeSet = {}
linkSet = {}
passengerSet = {}
weights = [1.0, 1.0, 1.0, 0.0] #IVT, WT, WK, TR

readZones()
readStops()
readTrips()
readSchedule()
readTransferLinks()
readAccessLinks()
readDemand()
sortConnectors()
assignPassengers("optimal")

