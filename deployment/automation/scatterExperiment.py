import json
import time

import requests
import paramiko
from humanfriendly import format_timespan, format_number
from apscheduler.schedulers.background import BackgroundScheduler

from csv_logger import CsvLogger
from tqdm import tqdm
import logging
from time import sleep

SYSTEM_MANAGER_URL = "<URL of system manager>"
CLIENT_SERVICE_ID = "<Service ID of the registered client service>" #Used to perform scale up and down of the clients

CLOUD_LATENCY = 200
EDGE_LATENCY = 20

PACKET_LOSS_HIGH = 0.08
PACKET_LOSS_MEDIUM = 0.01
PACKET_LOSS_LOW = 0.00001

BACKGROUND_JOB_INTERVAL = 60
DEPLOYMENT_WAITING_TIME = 10
DEPLOYMENT_COOLDOWN_TIME = 10
UNDEPLOYMENT_COOL_DOWN = 240
CLIENT_DEPLOYMENT_WAIT_TIME = 60 * 1  # 1 MINUTE
EXPERIMENT_DURATION = 10 * 1  # 10 seconds
REPEAT_EXPERIMENT = 5  # 5 times


# Cluster machines HOSTNAMES and USERS used for SSH and SLAconfgiurations. 
# We assume the SSH certificates are correctly configured for the current machine. 
vms = {
    "E1": "E1 IP ADDRESS",
    "E2": "E2 IP ADDRESS",
    "client": "client IP ADDRESS",
}

users = {
    "E1": "USERNAME TO ACCESS E1",
    "E2": "USERNAME TO ACCESS E2",
    "client": "USERNAME TO ACCESS client",

}

# service permutations of
#   primary         sift            encoding         lsh              matching    stress
service_permutations = [
    ["E1", "E1", "E1", "E1", "E1"],
    ["E2", "E2", "E2", "E2", "E2"],
    ["E1", "E1", "E2", "E2", "E2"],
    ["E2", "E2", "E1", "E1", "E1"],
]

#   primary         sift            encoding         lsh              matching
service_replica_permutations = [
    [1, 1, 1, 1, 1],
    [1, 2, 2, 1, 2],
    [1, 2, 1, 1, 2],
    [1, 3, 2, 1, 3],

]

# latency configurations for
#   E1, E2, client
hardware_latencies = [
    [0, 0, 0],
    #[CLOUD_LATENCY, EDGE_LATENCY, EDGE_LATENCY],
]

packet_loss_permutations = [
    PACKET_LOSS_LOW,
    #PACKET_LOSS_MEDIUM,
    #PACKET_LOSS_HIGH
]

scaling_permutations = [
    #1,
    4 #from 1 to 4 clients, 1 new client every CLIENT_DEPLOYMENT_WAIT_TIME interval
]

deployment_descriptor = {
    "sla_version": "v2.0",
    "customerID": "Admin",
    "applications": [
        {
            "applicationID": "",
            "application_name": "pipeline",
            "application_namespace": "percomm",
            "application_desc": "Demo pipeline",
            "microservices": [
                {
                    "microserviceID": "",
                    "microservice_name": "primary",
                    "microservice_namespace": "deploy",
                    "virtualization": "container",
                    "cmd": ["/bin/bash", "-c",
                            "cd home/ar_server/lib/cudasift && rm CMakeCache.txt && sed -i 's/-arch=sm_75/-arch=sm_30/g' CMakeLists.txt && sed -i 's/-arch=sm_25/-arch=sm_30/g' CMakeLists.txt && sed -i 's/executable/library/g' CMakeLists.txt && cmake -G 'Unix Makefiles' -DCMAKE_BUILD_TYPE=Release . && make && cd ../../build && make && cd ../ && ./server primary 10.30.100.1 false"],
                    "health-check": ["/bin/bash", "-c", "sleep 10"],
                    "memory": 1000,
                    "vcpus": 1,
                    "vgpus": 0,
                    "vtpus": 0,
                    "bandwidth_in": 0,
                    "bandwidth_out": 0,
                    "storage": 0,
                    "code": "ghcr.io/cao-jacky/ar_server:20230131_1034",
                    "state": "",
                    "port": "50001:50001/udp",
                    "addresses": {
                        "rr_ip": "10.30.100.1"
                    },
                    "constraints": [
                        {
                            "type": "direct",
                            "node": "xavier1",
                            "cluster": "gpu"
                        }
                    ],
                    "connectivity": [],
                    "added_files": []
                },
                {
                    "microserviceID": "",
                    "microservice_name": "sift",
                    "microservice_namespace": "deploy",
                    "virtualization": "container",
                    "cmd": ["/bin/bash", "-c",
                            "cd home/ar_server/lib/cudasift && rm CMakeCache.txt && sed -i 's/-arch=sm_75/-arch=sm_30/g' CMakeLists.txt && sed -i 's/-arch=sm_25/-arch=sm_30/g' CMakeLists.txt && sed -i 's/executable/library/g' CMakeLists.txt && cmake -G 'Unix Makefiles' -DCMAKE_BUILD_TYPE=Release . && make && cd ../../build && make && cd ../ && ./server sift 10.30.100.1 false"],
                    "health-check": ["/bin/bash", "-c", "sleep 10"],
                    "memory": 1000,
                    "vcpus": 1,
                    "vgpus": 1,
                    "vtpus": 0,
                    "bandwidth_in": 0,
                    "bandwidth_out": 0,
                    "storage": 0,
                    "code": "ghcr.io/cao-jacky/ar_server:20230131_1034",
                    "state": "",
                    "addresses": {
                        "rr_ip": "10.30.101.1"
                    },
                    "constraints": [
                        {
                            "type": "direct",
                            "node": "xavier1",
                            "cluster": "gpu"
                        }
                    ],
                    "connectivity": [],
                    "added_files": []
                },
                {
                    "microserviceID": "",
                    "microservice_name": "encoding",
                    "microservice_namespace": "deploy",
                    "virtualization": "container",
                    "cmd": ["/bin/bash", "-c",
                            "cd home/ar_server/lib/cudasift && rm CMakeCache.txt && sed -i 's/-arch=sm_75/-arch=sm_30/g' CMakeLists.txt && sed -i 's/-arch=sm_25/-arch=sm_30/g' CMakeLists.txt && sed -i 's/executable/library/g' CMakeLists.txt && cmake -G 'Unix Makefiles' -DCMAKE_BUILD_TYPE=Release . && make && cd ../../build && make && cd ../ && ./server encoding 10.30.100.1 false"],
                    "health-check": ["/bin/bash", "-c", "sleep 15"],
                    "memory": 1000,
                    "vcpus": 1,
                    "vgpus": 1,
                    "vtpus": 0,
                    "bandwidth_in": 0,
                    "bandwidth_out": 0,
                    "storage": 0,
                    "code": "ghcr.io/cao-jacky/ar_server:20230131_1034",
                    "state": "",
                    "addresses": {
                        "rr_ip": "10.30.102.1"
                    },
                    "constraints": [
                        {
                            "type": "direct",
                            "node": "xavier1",
                            "cluster": "gpu"
                        }
                    ],
                    "connectivity": [],
                    "added_files": []
                },
                {
                    "microserviceID": "",
                    "microservice_name": "lsh",
                    "microservice_namespace": "deploy",
                    "virtualization": "container",
                    "cmd": ["/bin/bash", "-c",
                            "cd home/ar_server/lib/cudasift && rm CMakeCache.txt && sed -i 's/-arch=sm_75/-arch=sm_30/g' CMakeLists.txt && sed -i 's/-arch=sm_25/-arch=sm_30/g' CMakeLists.txt && sed -i 's/executable/library/g' CMakeLists.txt && cmake -G 'Unix Makefiles' -DCMAKE_BUILD_TYPE=Release . && make && cd ../../build && make && cd ../ && ./server lsh 10.30.100.1 false"],
                    "health-check": ["/bin/bash", "-c", "sleep 10"],
                    "memory": 1000,
                    "vcpus": 1,
                    "vgpus": 1,
                    "vtpus": 0,
                    "bandwidth_in": 0,
                    "bandwidth_out": 0,
                    "storage": 0,
                    "code": "ghcr.io/cao-jacky/ar_server:20230131_1034",
                    "state": "",
                    "addresses": {
                        "rr_ip": "10.30.103.1"
                    },
                    "constraints": [
                        {
                            "type": "direct",
                            "node": "xavier1",
                            "cluster": "gpu"
                        }
                    ],
                    "connectivity": [],
                    "added_files": []
                },
                {
                    "microserviceID": "",
                    "microservice_name": "matching",
                    "microservice_namespace": "deploy",
                    "virtualization": "container",
                    "cmd": ["/bin/bash", "-c",
                            "cd home/ar_server/lib/cudasift && rm CMakeCache.txt && sed -i 's/-arch=sm_75/-arch=sm_30/g' CMakeLists.txt && sed -i 's/-arch=sm_25/-arch=sm_30/g' CMakeLists.txt && sed -i 's/executable/library/g' CMakeLists.txt && cmake -G 'Unix Makefiles' -DCMAKE_BUILD_TYPE=Release . && make && cd ../../build && make && cd ../ && ./server matching 10.30.100.1 false"],
                    "health-check": ["/bin/bash", "-c", "sleep 10"],
                    "memory": 1000,
                    "vcpus": 1,
                    "vgpus": 1,
                    "vtpus": 0,
                    "bandwidth_in": 0,
                    "bandwidth_out": 0,
                    "storage": 0,
                    "code": "ghcr.io/cao-jacky/ar_server:20230131_1034",
                    "state": "",
                    "addresses": {
                        "rr_ip": "10.30.104.1"
                    },
                    "constraints": [
                        {
                            "type": "direct",
                            "node": "xavier1",
                            "cluster": "gpu"
                        }
                    ],
                    "connectivity": [],
                    "added_files": []
                }
            ]
        }
    ]
}

filename = 'logs/deployment.csv'
delimiter = ';'
level = logging.INFO
custom_additional_levels = ['EXPERIMENT_START', 'EXPERIMENT_END', 'DEPLOY_START', 'DEPLOY_END', 'UNDEPLOY', 'BANDWIDTH',
                            'LATENCY', 'CLIENT_UP',
                            'CLIENT_DOWN']
fmt = f'%(asctime)s{delimiter}MONITORING{delimiter}%(levelname)s{delimiter}%(message)s'
datefmt = '%s'
header = ['timestamp', 'service', 'event', 'value']
csvlogger = CsvLogger(filename=filename,
                      delimiter=delimiter,
                      level=level,
                      add_level_names=custom_additional_levels,
                      add_level_nums=None,
                      fmt=fmt,
                      datefmt=datefmt,
                      header=header)


## Oakestra Login
def getlogin():
    url = "http://" + SYSTEM_MANAGER_URL + "/api/auth/login"
    credentials = {
        "username": "Admin",
        "password": "Admin"
    }
    r = requests.post(url, json=credentials)
    return r.json()["token"]

def get_csv_logger():
    return csvlogger


## Set latency in client machine
def set_latencies_and_loss(latencies,loss):
    print("\t Setting latencies: " + str(latencies))
    print("\t Setting CLIENT latency to: " + str(latencies[2]))
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(vms["client"], username=users["client"])
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(
        "echo " + "Passw0rd!" + " | sudo -S tc qdisc change dev enp3s0 root netem delay " + str(
            latencies[2]) + "ms 10ms 20% loss "+str(loss) + "%", timeout=15)
    result = ssh_stdout.readline()
    ssh.close()
    print(result)
    print(ssh_stderr.readline())


## Set loss in client machine
def set_packet_loss(loss):
    print("\t Setting packetloss: " + str(loss))
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(vms["esprimo"], username=users["esprimo"], password="Passw0rd!")
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(
        "echo " + "Passw0rd!" + " | sudo -S tc qdisc change dev enp3s0 root netem loss" + str(
            loss) + "%", timeout=15)
    result = ssh_stdout.readline()
    ssh.close()
    print(result)
    print(ssh_stderr.readline())


## Register pipeline in Oakestra root
def register_permutation(permutation):
    print("\t Registering permutation: " + str(permutation))

    # update the deployment descriptor
    for i in range(len(permutation)):
        deployment_descriptor["applications"][0]["microservices"][i]["constraints"][0]["node"] = permutation[i]

    # print(deployment_descriptor)
    head = {'Authorization': "Bearer " + API_TOKEN}
    url = "http://" + SYSTEM_MANAGER_URL + "/api/application"
    resp = requests.post(url, headers=head, json=deployment_descriptor)
    print(str(resp.request.headers))
    if resp.status_code == 200:
        json_resp = json.loads(resp.json())
        for app in json_resp:
            if app.get("application_name") == "pipeline":
                json_resp = app
                break
        return json_resp.get("applicationID"), json_resp.get("microservices")
    print(resp)
    return "", []


## Deploy pipeline in Oakestra root
def deploy_all(microservices, replicas):
    deployment_list = []
    for i in range(len(replicas)):
        for j in range(replicas[i]):
            deployment_list.append(microservices[i])

    head = {'Authorization': 'Bearer {}'.format(API_TOKEN)}
    logger = get_csv_logger()
    resp = {}
    for service in deployment_list:
        url = "http://" + SYSTEM_MANAGER_URL + "/api/service/" + service + "/instance"
        resp = requests.post(url, headers=head)
        time.sleep(DEPLOYMENT_WAITING_TIME)
    logger.DEPLOY_END(json.dumps({"status": resp.status_code}))



## Check pipeline deployment status in Oakestra root
def check_deployment(microservices):
    time.sleep(DEPLOYMENT_COOLDOWN_TIME)
    head = {'Authorization': 'Bearer {}'.format(API_TOKEN)}
    for microservice in microservices:
        url = "http://" + SYSTEM_MANAGER_URL + "/api/service/" + microservice
        resp = requests.get(url, headers={'Authorization': 'Bearer {}'.format(API_TOKEN)})
        if resp.status_code == 200:
            json_resp = json.loads(resp.json())
            instances = json_resp["instance_list"]
            if instances is not None:
                for instance in instances:
                    try:
                        if instance["status"] != "RUNNING":
                            return False, str(json_resp["microservice_name"])
                    except:
                        return False, str(json_resp["microservice_name"])
            else:
                return False, "No instances"
    return True, ""


## Undeploy pipeline in Oakestra root
def undeploy_all(app_id):
    print("\t Asking Undeployment")
    url = "http://" + SYSTEM_MANAGER_URL + "/api/application/" + str(app_id)
    resp = requests.delete(url, headers={'Authorization': 'Bearer {}'.format(API_TOKEN)})
    time.sleep(DEPLOYMENT_WAITING_TIME)
    pass


## Add a client instance in Oakestra root
def scale_up_client(amount):
    print("\t Asking client scaleup")
    logger = get_csv_logger()
    for i in range(amount):
        url = "http://" + SYSTEM_MANAGER_URL + "/api/service/" + CLIENT_SERVICE_ID + "/instance"
        resp = requests.post(url, headers={'Authorization': 'Bearer {}'.format(API_TOKEN)})
        logger.CLIENT_UP(json.dumps({"clients": i}))
        time.sleep(CLIENT_DEPLOYMENT_WAIT_TIME)
    pass


## Remove all active client instances, it does NOT delete the application.
def delete_clients(amount):
    print("\t Asking client Undeployment")
    url = "http://" + SYSTEM_MANAGER_URL + "/api/service/" + CLIENT_SERVICE_ID
    resp = requests.get(url, headers={'Authorization': 'Bearer {}'.format(API_TOKEN)})
    logger = get_csv_logger()
    logger.CLIENT_DOWN(json.dumps({"clients": 0}))
    if resp.status_code == 200:
        json_resp = json.loads(resp.json())
        instances = json_resp["instance_list"]
        if instances is not None:
            for instance in instances:
                url = "http://" + SYSTEM_MANAGER_URL + "/api/service/" + CLIENT_SERVICE_ID + "/instance/" + str(
                    instance["instance_number"])
                requests.delete(url, headers={'Authorization': 'Bearer {}'.format(API_TOKEN)})
        else:
            return False, "No instances"


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    API_TOKEN=getlogin()
    print("___________________")
    print("Xperiment forecasts")
    # n.service permutation * 2 (2 tests, one with single client and one scaling the clients) *  n. latency permutation * n.packetloss permutation
    permutations = len(service_permutations) * len(scaling_permutations) * len(hardware_latencies) * len(
        packet_loss_permutations) * len(service_replica_permutations)
    print("Number of permutations: " + str(permutations))
    seconds = permutations * REPEAT_EXPERIMENT * (
            DEPLOYMENT_WAITING_TIME + UNDEPLOYMENT_COOL_DOWN + EXPERIMENT_DURATION + DEPLOYMENT_WAITING_TIME *
            scaling_permutations[0])
    print("Expected Duration: " + str(format_timespan(seconds)))
    datapoints = permutations * (EXPERIMENT_DURATION * REPEAT_EXPERIMENT * 5 * 10)
    print("Expected Datapoints: " + str(format_number(datapoints)))
    print("___________________")
    print("EXPERIMENT STARTING")

    tot_permutations_concluded = 0
    logger = get_csv_logger()
    for latency in tqdm(hardware_latencies, desc="latency permutation", position=0):
        for loss in tqdm(packet_loss_permutations, desc="packet loss permutation", position=1):
            for permutation in tqdm(service_permutations, desc="service permutation", position=2):
                for scaling in tqdm(scaling_permutations, desc="scaling permutation", position=3):
                    for replicas in tqdm(service_replica_permutations, desc="replica permutation", position=4):

                        print("Experiment setup:")
                        print("\t Latency: " + str(latency) + " Packet Loss: " + str(loss))
                        print("\t Permutation: " + str(permutation))
                        print("\t Amount of clients: " + str(scaling))
                        print("\t Repetition number: " + str(REPEAT_EXPERIMENT))
                        print("\t Replicas number: " + str(replicas))
                        print("Experiment:")
                        #set_latencies_and_loss(latency,loss)
                        #set_packet_loss(loss)
                        logger.EXPERIMENT_START(
                            {"permutation": permutation, "replicas": replicas, "scaling": scaling, "latencies": latency,
                             "packet_loss": loss})

                        for repeat in tqdm(range(REPEAT_EXPERIMENT), desc="experiment repeat", position=5):
                            succeded = False
                            while succeded is False:
                                print("\t ####### Repetition : " + str(repeat))
                                print("App registration")
                                appid, microservices = register_permutation(permutation)
                                print("\t Deploy app")
                                deploy_all(microservices, replicas)
                                time.sleep(DEPLOYMENT_COOLDOWN_TIME)
                                success, instance = check_deployment(microservices)
                                if success:
                                    succeded = True
                                    logger.DEPLOY_START(
                                        {"permutation": permutation, "replicas": replicas, "scaling": scaling,
                                         "latencies": latency,
                                         "packet_loss": loss})
                                    print("\t Deploy clients")
                                    scale_up_client(scaling)
                                    print("\t Awaiting experiment to end")
                                    success, instance = check_deployment([CLIENT_SERVICE_ID])
                                    time.sleep(EXPERIMENT_DURATION)
                                    logger.UNDEPLOY(json.dumps({"app": appid}))
                                    print("\t Undeploy clients")
                                    delete_clients(replicas)
                                if not success:
                                    print("__________________")
                                    print("DEPLOYMENT_ERROR: ")
                                    print(permutation)
                                    print(loss)
                                    print(latency)
                                    print(instance)
                                    print("__________________")

                                print("\t Undeploy app")
                                undeploy_all(appid)
                                time.sleep(UNDEPLOYMENT_COOL_DOWN)

                        tot_permutations_concluded = tot_permutations_concluded + 1

                        logger.EXPERIMENT_END(
                            {"permutation": permutation, "replicas": replicas, "scaling": scaling, "latencies": latency,
                             "packet_loss": loss})

