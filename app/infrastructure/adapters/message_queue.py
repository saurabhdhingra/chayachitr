import json
from kafka import KafkaProducer, errors
from app.core.config import settings
from app.domain.entities.image import Transformation


class KafkaProducerAdapter:

    def __init__(self):
        try:
            self.producer = KafkaProducer(
                bootstrap_servers = settings.KAFKA_TRANSFORMATION_TOPIC.split('.'),
                value_serializer = lambda v : json.dumps(v).encode('utf-8'),
                api_version = (0, 10, 1),
                retries = 3
            )

            self.producer.send(settings.KAFKA_TRANSFORMATION_TOPIC, value = {"message": "System check"}).get(timeout = 5)
            print("Kafka Producer connected successfully.")
        
        except errors.NoBrokersAvailable:
            print("WARNING: Kafka broker not available. Image transformations will fail.")
            self.producer = None
        except Exception as e:
            print(f"WARNING: Kafka connection failed: {e}. Image transformation requests will fail.")
            self.producer = None

        self.topic = settings.KAFKA_TRANSFORMATION_TOPIC

    def send_transformation_request(self, original_image_id: str, new_image_id: str, transformation: Transformation, user_id: int):
        """
        Sends a request to the transformation topic.
        """

        if not self.producer: 
            raise ConnectionError("Kafka is not available. Cannot process asynchronous transformation.")

        message = {
            "original_id": original_image_id,
            "new_id": new_image_id,
            "user_id": user_id,
            "transformations": transformations.model_dump(exclude_none = True),
        }

        future = self.producer.send(self.topic, value = message)
        self.producer.flush()
        return future