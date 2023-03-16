# Import flask and requests modules
from flask import Flask, request
import json
import requests
import pika
import time

# ########################################## Setting up Notification Server

# Create a flask app
app = Flask(__name__)

# Create RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost', heartbeat=600,
                                       blocked_connection_timeout=300))
channel = connection.channel()
channel.queue_declare(queue='MyMQ')

# ########################################## Setting up Rate limiter
rate_limiter = {}

# Define a route for the API
@app.route("/notify", methods=["POST"])
def notify():
    json_str = json.dumps(request.json)
    if json_str in rate_limiter:
        # Calculate delta since last message
        delta = time.time() - rate_limiter[json_str]
        # If more then 1 same message in 5 second deny it
        if delta < 5:
            return "Failed: Notifing too frequently. Retry after 5 seconds"
    
    channel.basic_publish(exchange='',
                        routing_key='MyMQ',
                        body=json_str)
    rate_limiter[json_str] = time.time()
    return "Success"

# Run the app
if __name__ == "__main__":
    # Web server
    app.run(debug=True)
