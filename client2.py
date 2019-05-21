import json
import uuid

import pika


# Clase para manejar obtener el JWT
class MessageBrokerClient:

    def __init__(self, queue_name):
        # El key del canal
        self.routing_key = queue_name
        # Las credenciales del servidor RabbitMQ
        self.credentials = pika.PlainCredentials('atpos', 'atpos')

        # La información de conexión con la dirección del servidor
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='157.230.14.37', port=5672, virtual_host='/', credentials=self.credentials))

        # Inicia el canal
        self.channel = self.connection.channel()

        # Inicia una cola para recibir la respuesta
        result = self.channel.queue_declare('', exclusive=True)
        self.callback_queue = result.method.queue

        # Empieza a escuchar sobre el canal de respuesta
        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True)

    # Si recibe una respuesta sobre el canal de respuestas con su id guarda la respuesta
    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    # Manda un mensaje de autenticación y espera la respuesta
    def send_message(self, body):
        # Iniciliza la respuesta como None y un id para identificar su respuesta en el canal
        self.response = None
        self.corr_id = str(uuid.uuid4())

        # Publica el nombre de usuario y contraseña en el canal para que el servidor lo autentique
        self.channel.basic_publish(
            exchange='',
            routing_key=self.routing_key,
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=body)

        # Espera a recibir la respuesta y la devuelve
        while self.response is None:
            self.connection.process_data_events()
        return self.response


# while True:
#     # Obtiene un token
#     obtain_token = MessageBrokerClient(queue_name='obtener_jwt')
#     body = json.dumps({'user': '1234', 'password': str(5)})
#     response = obtain_token.send_message(body)
#     print(" [.] Got %r" % response)
#
#     token = json.loads(response)['token']
#
#     # Valida el token
#     validate_token = MessageBrokerClient(queue_name='validar_jwt')
#     body = json.dumps({'token': token})
#     response = validate_token.send_message(body)
#     print(" [.] Got %r" % response)
#
#     time.sleep(0.01)
#     break


def login(username, password):
    obtain_token_broker = MessageBrokerClient(queue_name='obtener_jwt')
    body = json.dumps({'user': username, 'password': password})
    response = obtain_token_broker.send_message(body)
    response = json.loads(response)

    if 'error' in response:
        raise Exception('Login fallido')

    else:
        return response


def validate_token(token):
    validate_token_broker = MessageBrokerClient(queue_name='validar_jwt')
    body = json.dumps({'token': token})
    response = validate_token_broker.send_message(body)
    response = json.loads(response.decode('utf-8'))

    if 'error' in response:
        raise Exception('Login fallido')

    else:
        return response


#token = login('1234', '5')['token']
#validate = validate_token(token)
#print(validate)
