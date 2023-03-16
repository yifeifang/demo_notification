# Import flask and requests modules
from flask import Flask, request
import json
import requests
import pika

# ########################################## Setting up Notification Server

# Create a flask app
app = Flask(__name__)

# Create RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost', heartbeat=600,
                                       blocked_connection_timeout=300))
channel = connection.channel()
channel.queue_declare(queue='MyMQ')

# Define a route for the API
@app.route("/notify", methods=["POST"])
def notify():
    channel.basic_publish(exchange='',
                      routing_key='MyMQ',
                      body=json.dumps(request.json))
    return "Success"

# Run the app
if __name__ == "__main__":
    # Web server
    app.run(debug=True)
