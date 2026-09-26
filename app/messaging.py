import json

import pika
from flask import current_app


def publish_event(event_type, payload):
    connection = pika.BlockingConnection(
        pika.URLParameters(current_app.config["RABBITMQ_URL"])
    )
    try:
        channel = connection.channel()
        queue = current_app.config["RABBITMQ_QUEUE"]
        channel.queue_declare(queue=queue, durable=True)
        channel.basic_publish(
            exchange="",
            routing_key=queue,
            body=json.dumps({"type": event_type, "payload": payload}),
            properties=pika.BasicProperties(
                content_type="application/json",
                delivery_mode=pika.DeliveryMode.Persistent,
            ),
        )
    finally:
        connection.close()