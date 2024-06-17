from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# Orchestrator URL
orchestrator_url = 'http://localhost:5002'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_test', methods=['POST'])
def start_test():
    test_type = request.form.get('test_type')

    if test_type not in ["AVALANCHE", "TSUNAMI"]:
        return jsonify({"error": "Invalid testing type. Please choose AVALANCHE or TSUNAMI."}), 400

    payload = {
        "test_type": test_type,
        "test_message_delay": 0 if test_type == "AVALANCHE" else 1,
        "message_count_per_driver": 100 if test_type == "AVALANCHE" else 300
    }

    response = requests.post(f'{orchestrator_url}/startTest', json=payload)

    if response.status_code == 200:
        return jsonify({"message": "Load test triggered successfully!"}), 200
    else:
        return jsonify({"error": f"Failed to trigger load test. Status code: {response.status_code}"}), 500

if __name__ == '__main__':
    app.run(debug=True)

