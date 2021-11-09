from datetime import datetime, timedelta
import socket
import sys
import argparse
import signal

# KeyboardInterrupt handler
def sigint_handler(signal, frame):
    print('KeyboardInterrupt is caught. Close all sockets :)')
    sys.exit(0)

# send trigger to printAll at servers
def sendPrintAll(serverSocket):
    serverSocket.send(b"printAll\n")

# Parse available severnames
def parseServernames(binaryServernames):
    return binaryServernames.decode().split(',')[:-1]


# get the completed file's name, what you want to do?
def getCompletedFilename(filename):
    ####################################################
    #                      TODO                        #
    # You should use the information on the completed  #
    # job to update some statistics to drive your      #
    # scheduling policy. For example, check timestamp, #
    # or track the number of concurrent files for each #
    # server?                                          #
    ####################################################

    completion_time = (datetime.now() - job_start_time.get(filename)).total_seconds()
    server_capacity = int(job_sizes.get(filename) / completion_time)

    server_index = job_to_server.get(filename)

    if server_capacity != server_capacities[server_index]:
        print("!!! Updating server capacity of server {}: capacity {} !!!".format(server_index, server_capacity))
        server_capacities[server_index] = server_capacity
    
    server_occupied[server_index] = False

    # In this example. just print message
    print(f"[JobScheduler] Filename {filename} is finished.")

# formatting: to assign server to the request
def scheduleJobToServer(servername, request):
    return (servername + "," + request + "\n").encode()

# main part you need to do
def assignServerToRequest(servernames, request):
    ####################################################
    #                      TODO                        #
    # Given the list of servers, which server you want #
    # to assign this request? You can make decision.   #
    # You can use a global variables or add more       #
    # arguments.                                       #

    request_name = request.split(",")[0]
    request_size = request.split(",")[1]
    job_sizes.update({request_name: int(request_size)})

    print("Filename: {}, Size: {}".format(request_name, request_size))

    server_to_send = None
    max_capacity = 0
    max_capacity_server_index = 0

    for index in range(0, len(servernames)):
        
        # compute server w largest cap too
        if server_capacities[index] > max_capacity:
            max_capacity = server_capacities[index]
            max_capacity_server_index = index

        # assign to server as long as not busy
        if not server_occupied[index]:
            server_to_send = servernames[index]
            job_to_server.update({request_name: index})
            job_start_time.update({request_name: datetime.now()})
            server_occupied[index] = True
            break

    # if no assigned server, gib to server with largest cap
    if server_to_send is None:
        server_to_send = servernames[max_capacity_server_index]
        job_to_server.update({request_name: max_capacity_server_index})
        job_start_time.update({request_name: datetime.now()})
        server_occupied[index] = True

    ####################################################

    # Schedule the job
    scheduled_request = scheduleJobToServer(server_to_send, request)
    return scheduled_request


def parseThenSendRequest(clientData, serverSocket, servernames):
    # print received requests
    print(f"[JobScheduler] Received binary messages:\n{clientData}")
    print(f"--------------------")
    # parsing to "filename, jobsize" pairs
    requests = clientData.decode().split("\n")[:-1]

    sendToServers = b""
    for request in requests:
        if request[0] == "F":
            # if completed filenames, get the message with leading alphabet "F"
            filename = request.replace("F", "")
            getCompletedFilename(filename)  
        else:
            # if requests, add "servername" front of the pairs -> "servername, filename, jobsize"
            sendToServers = sendToServers + \
                assignServerToRequest(servernames, request)  

    # send "servername, filename, jobsize" pairs to servers
    if sendToServers != b"":
        serverSocket.send(sendToServers)


if __name__ == "__main__":
    # catch the KeyboardInterrupt error in Python
    signal.signal(signal.SIGINT, sigint_handler)

    # parse arguments and get port number
    parser = argparse.ArgumentParser(description="JobScheduler.")
    parser.add_argument('-port', '--server_port', action='store', type=str, required=True,
                        help='port to server/client')
    args = parser.parse_args()
    server_port = int(args.server_port)

    # open socket to servers
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.connect(('127.0.0.1', server_port))

    # IMPORTANT: for 50ms granularity of emulator
    serverSocket.settimeout(0.0001)

    # receive preliminary information: servernames (can infer the number of servers)
    binaryServernames = serverSocket.recv(4096)
    servernames = parseServernames(binaryServernames)

    # initialize variables
    job_sizes = {}
    server_occupied = [ False for servername in servernames ]
    server_capacities = [ 0 for servername in servernames ]
    job_to_server = {}
    job_start_time = {}

    print(f"Servernames: {servernames}")

    currSeconds = -1
    now = datetime.now()
    while (True):
        try:
            # receive the completed filenames from server
            completeFilenames = serverSocket.recv(4096)
            if completeFilenames != b"":
                parseThenSendRequest(
                    completeFilenames, serverSocket, servernames)
        except socket.timeout:
            # IMPORTANT: catch timeout exception, DO NOT REMOVE
            pass

        # # Example printAll API : let servers print status in every seconds
        # if (datetime.now() - now).seconds > currSeconds:
        #     currSeconds = currSeconds + 1
        #     sendPrintAll(serverSocket)
