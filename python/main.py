import time

import paho.mqtt.client as mqtt
import json
from mysql.connector import connect, Error

print("System starting...")

eclipse_db = None
cursor = None

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker")

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("/sensor/#")
    client.subscribe("/log/#")


def on_disconnect(a, b, c):
    global eclipse_db, cursor

    print("Connection to MQTT broker lost, attempting to reconnect")
    while True:
        try:
            client.connect("mqtt", 1883, 60)
            break
        except:
            print("Retrying...")
            time.sleep(2)


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    global eclipse_db, cursor

    json_data = json.loads(msg.payload.decode())
    message_client = str(msg.topic).split("/").pop()

    message_topic = ""
    for val in str(msg.topic).split("/")[:-1]:
        message_topic += "/" + val

    if not eclipse_db.is_connected():
        print("Connection to MySql lost, attempting to reconnect")
        connect_mysql()

    if message_topic == "/log":
        sql = "INSERT INTO log (`client`, `status`, `time`, `context`) VALUES (%s,%s,%s,%s)"
        data = (message_client, json_data['status'], json_data['time'], json_data['context'])
    else:
        sql = "INSERT INTO messages (`client`, `topic`, `payload`) VALUES (%s,%s,%s)"
        data = (message_client, message_topic, json.dumps(json_data))

    while True:
        try:

            cursor.execute(sql, data)
            eclipse_db.commit()
            break

        except Error as e:
            if not eclipse_db.is_connected():
                print("Connection to MySql lost, attempting to reconnect")
                connect_mysql()
            else:
                print(str(e) + ", Retying...")
            time.sleep(2)


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

            eclipse_db, cursor = eclipse_db_conn, cursor_conn
            return

        except Error as e:
            print(str(e) + ", Retrying...")
            time.sleep(2)


connect_mysql()

client = mqtt.Client()
client.username_pw_set("python", "python")
client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect

# attempt to connect to broker using disconnect function
# on_disconnect()

client.connect("mqtt", 1883, 60)

print("System startup complete")

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()
