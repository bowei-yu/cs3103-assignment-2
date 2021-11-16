# CS3103 Assignment 2 - Job Scheduling
### Done by: Wong Jun Long (A021889W) and Yu Bowei (A0205496Y)

</br>

# Instructions to run job scheduler
### 1. Use a linux environment with Python 3 and C installed (eg xcne1.comp.nus.edu.sg)
### 2. Start the server-client simulator on a terminal using:
`./server_client -port <port number> -prob 100`
### 3. Launch the job scheduler by running on another terminal:
`python3 jobScheduler.py -port <port number>`
#### Ensure that the port numbers for both programs are the same.
### 4. To terminate the programs, press CTRL-C for each of them within the CLI.

</br>

# Explanation of algorithm
Our job scheduler utilizes the weighted least response time algorithm. 

Initially, each server is assigned an equal weight of 100000. The job scheduler sends all servers a job upon receival, in the sequence the servers are presented in the `servernames` list, to get an initial gauge of their response times. 

For each server, the job scheduler keeps track of the weight, number of active connections and time which the server is sent a job. After a job is completed, the job scheduler calculates the `response time` of the server (`time job completion is received - time server is sent a job`). 

The weight for the server that completed the job is then computed using `response time * active connections * (100000 / (total number of servers - current index of server))`. This ensures that factors such as least response time and lower number of active connections are considered, as well as giving a server at the back of the line a relative better chance of being picked.

Subsequently, for each new job received by the job scheduler, the job scheduler will assign the job to the server with the least weight. 
