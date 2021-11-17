from datetime import datetime, timedelta
import socket
import sys
import argparse
import signal

server_list = []
initial_list = []
server_request_times = {}
job_queue = []

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
    global server_list, server_request_times, num_occupied, job_queue
    server_name = server_request_times[filename][0]
    request_time = server_request_times[filename][1]

    # get response time
    time_taken = (datetime.now() - request_time).total_seconds()

    # find four_tuple in server list
    four_tuple = None
    position = None
    for idx, val in enumerate(server_list):
        if server_name in val:
            four_tuple = val
            position = idx
            break

    # Update N value
    N = four_tuple[0]
    active_connections = four_tuple[1]
    response_time = four_tuple[2]
    response_time = time_taken
    active_connections = active_connections - 1

    N = response_time * active_connections
    weighted_response_time = N * (10000 / ((len(server_list) - (idx + 1) + 1)))

    # Update four_tuple in server_list and sort
    server_list[position][0] = weighted_response_time
    server_list[position][1] = active_connections
    server_list[position][2] = response_time
    server_list.sort()

    #if len(job_queue) > 0:
    #    scheduled_request = scheduleJobToServer(server_name, job_queue.pop(0))
    #else:
    
    print('Completed')
    print(server_list)

    # # Adjust connection weight (cW) = Number of Active Connections x (10000 / Set Weight (sW))
    # # Adjust time weight (cW) = Response Time x (10000 / Set Weight (sW))
    # # Blend predictions by averaging out N value, connection_weight, and time weight
    # for idx, val in enumerate(server_list):
    #     if server_name in val:
    #         weighted_response_time = N * (10000 / ((len(server_list) - (idx + 1) + 1)))
    #         server_list[idx][0] = (0.5 * N) + (0.5 * weighted_response_time)
    #         break
    # server_list.sort()


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
    ####################################################
    request_name = request.split(",")[0]
    request_size = request.split(",")[1]

    # # Example. just assign the first server
    # server_to_send = servernames[0]

    # Get variables
    global server_list, server_request_times, initial_list, num_occupied, job_queue

    # If servers are not initialized, initialize using initial list first (ie push out jobs and spread it across to all servers)
    if initial_list:
        four_tuple = initial_list.pop(0)
    else:
        four_tuple = server_list[0]

    N = four_tuple[0]
    active_connections = four_tuple[1]
    response_time = four_tuple[2]
    server_name = four_tuple[3]

    # Increment active connections
    server_to_send = server_name
    active_connections = active_connections + 1        

    if active_connections <= 1:
        for idx, val in enumerate(server_list):
            if server_name in val:
                server_list[idx][1] = active_connections
                # Prevents bug where N = 0 and only 1 server keeps getting assigned jobs
                if response_time != 0:
                    N = response_time * active_connections
                    weighted_response_time = N * (10000 / ((len(server_list) - (idx + 1) + 1)))
                    server_list[idx][0] = weighted_response_time
                break
        server_list.sort()

        print('Initial list')
        print(initial_list)
        print('Sent')
        print(server_list)

    # Record time of request to server
    # server_request_times[request_name] = [server_name, datetime.now()]

    # Schedule the job
        scheduled_request = scheduleJobToServer(server_to_send, request)
        server_request_times[request_name] = [server_name, datetime.now()]
        return scheduled_request
    else:
        # queue and send later
        job_queue.append(request)
        return None


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
            if len(job_queue) > 0:
                request = job_queue.pop()
                sendToServers = sendToServers + \
                        assignServerToRequest(servernames, request)
        else:
            # if requests, add "servername" front of the pairs -> "servername, filename, jobsize"
            assigned_request = assignServerToRequest(servernames, request)
            if assigned_request is not None:
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
    print(f"Servernames: {servernames}")

    for i in servernames:
        # (response time * number of active connections, servername, response time, number of active connections)
        response_time = 0
        active_connections = 0
        N = 100000
        server_list.append([N, active_connections, response_time, i])
    print(server_list)
    # For initializing all servers
    initial_list = server_list.copy()

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
