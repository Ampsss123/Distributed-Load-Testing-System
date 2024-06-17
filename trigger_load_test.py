import requests

# Take user input for the type of testing
test_type = input("Enter the type of testing (AVALANCHE / TSUNAMI): ").upper()

if test_type not in ["AVALANCHE", "TSUNAMI"]:
    print("Invalid testing type. Please choose AVALANCHE or TSUNAMI.")
    exit()

# Define test configuration based on user input
if test_type == "AVALANCHE":
    test_config = {
        "test_type": "AVALANCHE",
        "test_message_delay": 0,  # Minimal delay between messages
        "message_count_per_driver": 100 # Higher number of messages per driver
    }
elif test_type == "TSUNAMI":
    test_config = {
        "test_type": "TSUNAMI",
        "test_message_delay": 1,  # Short delay between messages
        "message_count_per_driver": 300 # Even higher number of messages per driver
    }

# Send the test configuration to the Orchestrator
response = requests.post('http://localhost:5002/startTest', json=test_config)

if response.status_code == 200:
    print("Response from orchestrator:", response)
    print("Load test triggered successfully!")
else:
    print("Failed to trigger load test. Status code:", response.status_code)

