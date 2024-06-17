from flask import Flask, jsonify

app = Flask(__name__)

request_count = 0
response_count = 0

@app.route('/',methods = ['GET'])
def hello():
    return "Local Server for load testing"

@app.route('/ping', methods=['GET'])
def ping():
    global request_count
    request_count += 1
    return jsonify({"message": "Ping received"})

@app.route('/metrics', methods=['GET'])
def metrics():
    global request_count, response_count
    return jsonify({
        "requests_sent": request_count,
        "responses_received": response_count
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)

