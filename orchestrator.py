from flask import Flask, jsonify, request
from kafka import KafkaProducer, KafkaConsumer
import uuid
import json
import threading
import time
import sys

app = Flask(__name__)

# Initialize Kafka Producer and Consumer
KAFKA_BROKER = 'localhost:9092'
producer = KafkaProducer(bootstrap_servers=KAFKA_BROKER)
consumer_o = KafkaConsumer(
    bootstrap_servers=KAFKA_BROKER,
    group_id='orchestrator-group',
    auto_offset_reset='earliest',
    enable_auto_commit=True
)
consumer_o.subscribe(['metrics_topic', 'heartbeats_topic','num_drivers'])
test_config = {}
active_drivers = set()
trigger_message = {}
node_id = ""
received_nodes = set()
num_drivers = 0

# In-memory storage for received metrics
metrics_store = {}
@app.route('/', methods=['POST'])
def consume_heartbeats():
    global active_drivers,num_drivers
    for msg in consumer_o:
        try:
            if msg is None:
                continue
            if msg.topic == 'num_drivers':
                num_drivers = int(msg.value.decode('utf-8'))
                print(num_drivers)

            if msg.topic == 'heartbeats_topic':
                heartbeat_data = json.loads(msg.value.decode('utf-8'))
                node_id = heartbeat_data.get('node_id')
                active_drivers.add(node_id)
                if len(active_drivers) == num_drivers:  # If both drivers are active
                    # Distribute load testing configurations
                    print("received heatbeats from driver nodes",num_drivers)
                    print(active_drivers)
                    distribute_configurations()

        except Exception as e:
            print("Error occurred while consuming heartbeats:", str(e))
            continue


@app.route('/startTest', methods=['POST'])
def start_test():
    global test_config,trigger_message
    test_config = request.json  # Contains test configurations
    print("received test_config:",test_config)
    trigger_message = {
        "test_id": str(uuid.uuid4()),  # Generate a unique test ID
        "trigger": "YES"
    }
    combined_message = {
        "test_config": test_config,
        "trigger_message": trigger_message
    }
    return jsonify(test_config)

@app.route('/aggregate',methods = ['GET'])


def aggregate():
    global metrics_store
    # Aggregate metrics across all nodes
    all_mean_latency = []
    all_mode_latency = []
    all_min_latency = []
    all_max_latency = []

    for node_metrics in metrics_store.values():
        for metrics in node_metrics:
            all_mean_latency.append(metrics['metrics']['mean_latency'])
            all_mode_latency.extend(metrics['metrics']['mode_latency'])
            all_min_latency.append(metrics['metrics']['min_latency'])
            all_max_latency.append(metrics['metrics']['max_latency'])

    # Calculate aggregated metrics
    aggregated_metrics = {
        'mean_latency': sum(all_mean_latency) / len(all_mean_latency) if all_mean_latency else None,
        'mode_latency': list(set(all_mode_latency)) if all_mode_latency else None,
        'min_latency': min(all_min_latency) if all_min_latency else None,
        'max_latency': max(all_max_latency) if all_max_latency else None
    }

    print(aggregated_metrics)
    print("-----COMPLETED ORCHESTRATOR CODE-----")
    return jsonify(aggregated_metrics)
    sys.exit()
   
   


@app.route('/testStatistics', methods=['GET'])
def display_metrics():
    global metrics_store
    print(metrics_store)
    aggregate()

    # Retrieve aggregated statistics from metrics_store for display

    return jsonify(metrics_store)


def distribute_configurations():
    global test_config
    global active_drivers
    driver_configurations = []
    total_drivers = len(active_drivers)
    messages_per_driver = test_config['message_count_per_driver'] // total_drivers

    for driver in active_drivers:
        if len(driver_configurations) < total_drivers - 1:
            config = test_config.copy()
            config['message_count_per_driver'] = messages_per_driver
            driver_configurations.append((driver, config))
        else:
            config = test_config.copy()
            # Adjust the message count for the last driver to ensure total consistency
            config['message_count_per_driver'] = test_config['message_count_per_driver'] - (messages_per_driver * (total_drivers - 1))
            driver_configurations.append((driver, config))

    producer.send('trigger_message',value=json.dumps(trigger_message).encode('utf-8'))
    print("Trigger to start load test sent successfully!")
    producer.flush()
    time.sleep(5)
    # Sending configurations to driver nodes
    print("Sending Config:",driver_configurations)
    producer.send("test_config",value=json.dumps(driver_configurations).encode('utf-8'))
    producer.flush()
    consume_metrics()


def consume_metrics():
    global metrics_store,num_drivers
    for msg in consumer_o:
        try:
            if msg is None:
                continue
            if msg.topic == 'metrics_topic':
                metrics_data = msg.value.decode('utf-8')
                metrics = json.loads(metrics_data)
                node_id = metrics.get('node_id')
                if node_id not in metrics_store:
                    metrics_store[node_id] = []
                metrics_store[node_id].append(metrics)
                received_nodes.add(node_id)
                print("Received metrics from Node:", node_id)
        except Exception as e:
            print("Error occurred while consuming metrics:", str(e))
            continue

    if len(received_nodes) == num_drivers:
        display_metrics()


if __name__ == '__main__':
    # Start consuming metrics in a separate thread
    heartbeat_thread = threading.Thread(target=consume_heartbeats)
    heartbeat_thread.start()

    #metrics_thread = threading.Thread(target=consume_metrics)
    #metrics_thread.start()

    # Run the Flask app
    app.run(host='0.0.0.0', port=5002)
