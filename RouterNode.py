#!/usr/bin/env python
import GuiTextArea, RouterPacket, F
from copy import deepcopy

class RouterNode():
    myID = None
    myGUI = None
    sim = None
    distanceTable = [] # 2D array of costs
    route = []

    def __init__(self, ID, sim, costs):
        self.myID = ID
        self.sim = sim
        self.myGUI = GuiTextArea.GuiTextArea(f"  Output window for Router #{self.myID}  ")

        self.costs = deepcopy(costs)
        self.distanceTable = [[0] * self.sim.NUM_NODES for _ in range(self.sim.NUM_NODES)]
        self.route = [0] * self.sim.NUM_NODES

        # Init distanceTable
        for i in range(self.sim.NUM_NODES):
            for j in range(self.sim.NUM_NODES):
                if i == j:
                    self.distanceTable[i][j] = 0
                elif i == self.myID:
                    self.distanceTable[i][j] = self.costs[j]
                else:
                    self.distanceTable[i][j] = self.sim.INFINITY

        # Init route
        for i in range(self.sim.NUM_NODES):
            self.route[i] = -1 if self.costs[i] == self.sim.INFINITY else i

        # Broadcast initial distance table to neighbors
        self.broadcast()
        self.printDistanceTable()

    def recvUpdate(self, pkt):
        # Update distance table
        self.distanceTable[pkt.sourceid] = pkt.mincost
        if(self.Bellman()):
            self.broadcast()

    def sendUpdate(self, pkt):
        # Poison reverse
        if (self.sim.POISONREVERSE):
            for i in range(self.sim.NUM_NODES):
                if self.route[i] == pkt.destid:
                    pkt.mincost[i] = self.sim.INFINITY

        self.sim.toLayer2(pkt)

    def printDistanceTable(self):
        self.myGUI.println(f"Current table for {self.myID} at time {self.sim.getClocktime()}")
        self.myGUI.println("Dest\tCost\tRoute")
        for i in range(self.sim.NUM_NODES):
            self.myGUI.println(f"{i}\t{self.distanceTable[self.myID][i]}\t{self.route[i]}")
        self.myGUI.println()

    def updateLinkCost(self, dest, newcost):
        self.myGUI.println(f"Link cost from {self.myID} to {dest} is now {newcost}\n")
        self.costs[dest] = newcost

        # Update the cost of the link
        self.distanceTable[self.myID][dest] = newcost
        self.distanceTable[dest][self.myID] = newcost

        self.broadcast()

    def broadcast(self):
        for i in range(self.sim.NUM_NODES):
            if i != self.myID and self.costs[i] != self.sim.INFINITY and self.route[i] != -1:

                self.sendUpdate(RouterPacket.RouterPacket(self.myID, i, deepcopy(self.distanceTable[self.myID])))

    def Bellman(self):
        changed = False
        # Bellman-Ford algorithm
        for i in range(self.sim.NUM_NODES):
            # Don't update self
            if i == self.myID:
                continue
            
            distanceToNextRouter = self.distanceTable[self.myID][self.route[i]]
            distanceNextRouterToDest = self.distanceTable[self.route[i]][i]
            estimatedRouteCost = distanceToNextRouter + distanceNextRouterToDest

            if self.distanceTable[self.myID][i] != estimatedRouteCost:
                self.distanceTable[self.myID][i] = estimatedRouteCost

                if self.distanceTable[self.myID][i] > self.costs[i]:
                    self.distanceTable[self.myID][i] = self.costs[i]
                    self.route[i] = i

                changed = True

            for j in range(self.sim.NUM_NODES):
                currentCost = self.distanceTable[self.myID][j]
                newCost = self.distanceTable[self.myID][i] + self.distanceTable[i][j]

                if newCost < currentCost:
                    self.distanceTable[self.myID][j] = newCost
                    self.route[j] = self.route[i]
                    changed = True

        return changed
