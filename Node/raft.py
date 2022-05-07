import time
import random

class RaftNode:
    def __init__(self, state="FOLLOWER", currentTerm=0, votedFor=None, log=[], voteCount=0):
        self.state = state
        self.currentTerm = currentTerm
        self.votedFor = votedFor
        self.log = log
        self.electionTimeout = self.getElectionTimeout()
        self.voteCount = voteCount
        self.startTime = time.perf_counter()
        self.currentLeader = ""
        self.shutdown = False
        self.heartbeatTimeout = self.getHeartbeatTimeout()
        self.commitIndex = -1
        self.lastApplied = 0
        self.nextIndex = []
        self.matchIndex = []
        self.committed = False

    def getElectionTimeout(self):
        return random.randint(1000, 10000)/1000.0

    def getHeartbeatTimeout(self):
        return 0.5

    def getLogIndex(self):
        return len(self.log) - 1

    def getLogTerm(self):
        if len(self.log) == 0:
            return 0
        entry = self.log[len(self.log)-1]
        return entry["term"]