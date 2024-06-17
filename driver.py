import requests
import json
import time
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
from collections import Counter
import threading
import uuid
import sys
import socket

# Kafka configuration
KAFKA_BROKER = 'localhost:9092'
producer = KafkaProducer(bootstrap_servers=KAFKA_BROKER)
# HTTP Server configuration
TARGET_SERVER_URL = 'http://localhost:8000'
PING_ENDPOINT = '/ping'
METRICS_ENDPOINT = '/metrics'

metrics_values = []  # Store response time metrics
load_test_started = False  # Flag to track load test start
register_message = {}
data = {}
test_config_store = {}
node_id = None
load_test_started = False

def mean(values):
    if not values:
        return None
    return round(sum(values) / len(values),3)

def median(values):
    if not values:
        return None
    sorted_values = sorted(values)
    length = len(sorted_values)
    if length % 2 == 0:
        return round((sorted_values[length // 2 - 1] + sorted_values[length // 2]) / 2,3)
    else:
        return round(sorted_values[length // 2],3)


def mode(data):
    rounded_data = [round(item, 3) for item in data]  # Round off the values to 3 decimal places
    freq_dict = Counter(rounded_data)

    max_freq = max(freq_dict.values())
    mode_result = [key for key, value in freq_dict.items() if value == max_freq]
    return mode_result

def send_request(node_id):
    # Send HTTP request to the target server
    start_time = time.time()
    response = requests.get(TARGET_SERVER_URL + PING_ENDPOINT)
    end_time = time.time()
    latency = end_time - start_time
    metrics_values.append(latency)  # Record response time metrics



def calculate_metrics(node_id):
    global metrics_values
    #print(metrics_values)
    mean_latency = mean(metrics_values)
    median_latency = median(metrics_values)
    min_latency = min(metrics_values)
    max_latency = max(metrics_values)
    mode_latency = mode(metrics_values)
    data = {
        "node_id": node_id,
        "report_id": str(uuid.uuid4()),
        "metrics": {
            "mean_latency": mean_latency,
            "median_latency": median_latency,
            "min_latency": min_latency,
            "max_latency": max_latency,
            "mode_latency": mode_latency if mode_latency else None
        }
    }
    producer.send('metrics_topic', json.dumps(data).encode('utf-8'))
    producer.flush()
    print("Driver", node_id, "Metrics sent:", data)


def testing():
    print("-----In testing-----", test_config_store)
    global load_test_started, metrics_values

    for test_config in test_config_store:
        node_id = test_config[0]
        test_type = test_config[1].get('test_type')
        message_count_per_driver = test_config[1].get('message_count_per_driver')
        delay = test_config[1].get('test_message_delay')

        if test_type and message_count_per_driver is not None and delay is not None:
            metrics_values = []
            print(f"Node {node_id} test")
            for _ in range(int(message_count_per_driver)):
                send_request(node_id)
                time.sleep(int(delay))  # Delay between requests
            calculate_metrics(node_id)
    
    print("-----COMPLETED DRIVER CODE-----")
    sys.exit()
    

def consume_configurations():
    global load_test_started, test_config_store
    consumer = KafkaConsumer(
        bootstrap_servers=KAFKA_BROKER,
        group_id='driver-group',
        auto_offset_reset='earliest',
        enable_auto_commit=True
    )
    consumer.subscribe(['test_config', 'trigger_message'])

    for msg in consumer:
        if msg is None:
            continue
        try:
            topic = msg.topic
            print(topic)
            config = json.loads(msg.value.decode('utf-8'))
            print("Config received:",config)
            if topic == 'trigger_message' and config.get('trigger') == 'YES' and not load_test_started:
                load_test_started = True  # Set flag to indicate load test started
                print("trigger_test received , testing()")

            if topic == 'test_config':
                print("test_config received",config)
                test_config_store = config

            if load_test_started and test_config_store:
                testing()

        except Exception as e:
            print("Error occurred while consuming messages:", str(e))

def heartbeat(node_id):
    while True:
        heartbeat_message = {
            "node_id": node_id,
            "heartbeat": "YES"
        }
        print("heartbeats:",heartbeat_message)
        producer.send('heartbeats_topic', json.dumps(heartbeat_message).encode('utf-8'))
        print("heartbeat message sent to orchestrator")
        producer.flush()
        consume_configurations()
        time.sleep(10)  # Adjust heartbeat interval as needed


def register_driver(node_id):
    heartbeat_thread = threading.Thread(target=heartbeat, args=(node_id,))
    heartbeat_thread.start()

if __name__ == '__main__':
    num_drivers = int(input("Enter the number of driver nodes (2-8): "))  # Number of driver nodes
    if num_drivers >= 2 and num_drivers <= 8:
        producer.send('num_drivers', str(num_drivers).encode('utf-8'))  # Send num_drivers as bytes
        print("sent num_drivers")
        producer.flush()
        threads = []
        print("-----main-----")
        for i in range(num_drivers):
            node_id = str(uuid.uuid4())
            t = threading.Thread(target=register_driver, args=(node_id,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

    else:
        print('Enter a number between 2-8')