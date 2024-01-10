import time

import paho.mqtt.client as mqtt
import json
from mysql.connector import connect, Error

print("System starting...")

# Initialize variables for MySQL connection
eclipse_db = None
cursor = None

# Callback for when the client receives a CONNACK response from the server
def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker")

    # Subscribe to relevant topics upon connecting
    client.subscribe("/sensor/#")
    client.subscribe("/log/#")

# Callback for when the client is disconnected from the broker
def on_disconnect():
    global eclipse_db, cursor

    print("Connection to MQTT broker lost, attempting to reconnect")
    while True:
        client.connect("mqtt", 1883, 60)
        print(client.is_connected())
        if client.is_connected():
            return
        time.sleep(2)

# Callback for when a PUBLISH message is received from the server
def on_message(client, userdata, msg):
    global eclipse_db, cursor

    # Decode the received JSON payload
    json_data = json.loads(msg.payload.decode())
    message_client = str(msg.topic).split("/").pop()

    message_topic = ""
    for val in str(msg.topic).split("/")[:-1]:
        message_topic += "/" + val

    # Reconnect to MySQL if connection is lost
    if not eclipse_db.is_connected():
        print("Connection to MySQL lost, attempting to reconnect")
        connect_mysql()

    if message_topic == "/log":
        # SQL query for log messages
        sql = "INSERT INTO log (`client`, `status`, `time`, `context`) VALUES (%s,%s,%s,%s)"
        data = (message_client, json_data['status'], json_data['time'], json_data['context'])
    else:
        # SQL query for sensor messages
        sql = "INSERT INTO messages (`client`, `topic`, `payload`) VALUES (%s,%s,%s)"
        data = (message_client, message_topic, json.dumps(json_data))

    # Retry executing the SQL query in case of an error
    while True:
        try:
            cursor.execute(sql, data)
            eclipse_db.commit()
            break

        except Error as e:
            if not eclipse_db.is_connected():
                print("Connection to MySQL lost, attempting to reconnect")
                connect_mysql()
            else:
                print(str(e) + ", Retrying...")
            time.sleep(2)

# Function to connect to MySQL database
def connect_mysql():
    global eclipse_db, cursor
    while True:
        try:
            eclipse_db_conn = connect(
                host="mysql",
                user="root",
                password="password",
                database="eclipse_db"
            )
            cursor_conn = eclipse_db_conn.cursor()
            print("Connected to database")

            # Update global variables
            eclipse_db, cursor = eclipse_db_conn, cursor_conn
            return

        except Error as e:
            print(str(e) + ", Retrying...")
            time.sleep(2)

# Initial MySQL connection
connect_mysql()

# MQTT client setup
client = mqtt.Client()
client.username_pw_set("python", "python")
client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect

# Connect to the MQTT broker
client.connect("mqtt", 1883, 60)

print("System startup complete")

# Blocking call that processes network traffic, dispatches callbacks, and handles reconnecting
client.loop_forever()
