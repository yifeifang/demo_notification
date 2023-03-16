import pika
import json
import apprise
import signal
import sys

# ########################################## Setting up Logging system
# Ctrl + C handler
def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    print('Dumping log...')
    mylog.flush()
    mylog.close()
    sys.exit(0)
# Open the Log file
mylog = open("log.log", 'w')
# Register the handle
signal.signal(signal.SIGINT, signal_handler)

# ########################################## Setting up 3rd Party Service
# Create an appriser object
myappriser = apprise.Apprise()
# Cached user info. This can be load from a file
myappriser.add('tgram://6276019144:AAHdcw7ifMpg1K_ZbBw0Faj5LLGWswfnsj8/724517549', tag='724517549')

# ########################################## Setting up Message Queue
# Connect to rabbit MQ
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
# declare queue
channel.queue_declare(queue='MyMQ')

# ########################################## Setting up Deduplicate DB
message_cache = {}

# ########################################## Setting up Message queue call back
def callback(ch, method, properties, body):
    json_str = body.decode('UTF-8')
    data = json.loads(str(json_str))
    # If data is valid
    if data and data["to"][0]["user_id"] and data["from"]["email"] and data["subject"] and data["content"]:
        success = myappriser.notify(title=data["subject"] + " from " + data["from"]["email"], body=data["content"], tag=str(data["to"][0]["user_id"]))
        if success:
            print("Successfully notified user")
            # Logging
            mylog.write("Success, {}\n".format(json_str))
            # Not good this is very slow as it will be io bounded
            mylog.flush()
        else:
            print("Failed notified user")
            # Logging
            mylog.write("Fail, {}\n".format(json_str))
            # Not good this is very slow as it will be io bounded
            mylog.flush()

            # Deduplicate
            if not json_str in message_cache:
                message_cache[json_str] = 1
            else:
                message_cache[json_str] += 1

            # Re-transmit
            if message_cache[json_str] < 3:
                channel.basic_publish(exchange='',
                        routing_key='MyMQ',
                        body=json_str)

# Starting consuming MQ
channel.basic_consume(queue='MyMQ',
                      auto_ack=True,
                      on_message_callback=callback)
print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()
