
import pika
import os
import math
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

class Analitica():
    influx_org = 'org'
    valor_maximo_temp = -math.inf
    valor_minimo_temp = math.inf
    valor_maximo_humedad = -math.inf
    valor_minimo_humedad = math.inf
    influx_bucket = 'rabbit'
    influx_token = 'TOKEN_SECRETO'
    influx_url = 'http://influxdb:8086'
    temperatura = 0
    humedad = 0
    temp_s = 0
    temp_h = 0 
    humed_s = 0
    humed_h = 0 

    def write_db(self, tag, key, value):
        client= InfluxDBClient(url=self.influx_url, token=self.influx_token, org=self.influx_org)
        write_api = client.write_api(write_options=SYNCHRONOUS)
        point = Point('Analitica').tag("Descripcion", tag).field(key, value)
        write_api.write(bucket=self.influx_bucket, record=point)

    def temperatura_maximo(self, _medida):
        if _medida > self.valor_maximo_temp:
            self.valor_maximo_temp = _medida
        self.write_db('Temperatura', "Maxima", self.valor_maximo_temp)
    
    def temperatura_minimo(self, _medida):
        if _medida < self.valor_minimo_temp:
            self.valor_minimo_temp = _medida
        self.write_db('Temperatura', "Minima", self.valor_minimo_temp)

    def promedio_temperatura(self, _medida):
        self.temp_h += 1
        self.temp_s += _medida
        mediana_temp = round((self.temp_s/self.temp_h),2)
        print("promedio Temperatura: {}°C".format(mediana_temp), flush=True)
        self.write_db('Temperatura', "promedio", mediana_temp)

    def Humedad_maximo(self, _medida):
        if _medida > self.valor_maximo_humedad:
            self.valor_maximo_humedad = _medida
        self.write_db('Humedad', "Maxima", self.valor_maximo_humedad)
    
    def humedad_minimo(self, _medida):
        if _medida < self.valor_minimo_humedad:
            self.valor_minimo_humedad = _medida
        self.write_db('Humedad', "Minima", self.valor_minimo_humedad)

    def humedad_promedio(self, _medida):
        self.humed_h += 1
        self.humed_s += _medida
        mediana_humedad = round((self.humed_s/self.humed_h),2)
        print("promedio Humedad Relativa: {}%".format(mediana_humedad), flush=True)
        self.write_db('Humedad', "promedio", mediana_humedad)

    def toma_medida(self, _mensaje):
        datos_sensor = _mensaje.split(",")
        medida_temp = float(datos_sensor[0])
        medida_humedad = float(datos_sensor[1])
        print("Temperatura: {}°C".format(datos_sensor[0]), " Humedad: {}%".format(datos_sensor[1]),flush=True)
        self.temperatura_maximo(medida_temp)
        self.temperatura_minimo(medida_temp)
        self.promedio_temperatura(medida_temp)
        self.Humedad_maximo(medida_humedad)
        self.humedad_minimo(medida_humedad)
        self.humedad_promedio(medida_humedad)
        
if __name__ == '__main__':

    analitica = Analitica()
    def callback(ch, method, properties, body):
        global analitica
        mensaje = body.decode("utf-8")
        analitica.toma_medida(mensaje)

    url = os.environ.get('AMQP_URL', 'amqp://guest:guest@rabbit:5672/%2f')
    params = pika.URLParameters(url)
    connection = pika.BlockingConnection(params)

    channel = connection.channel()
    channel.queue_declare(queue='mensajes')
    channel.queue_bind(exchange='amq.topic', queue='mensajes', routing_key='#')    
    channel.basic_consume(queue='mensajes', on_message_callback=callback, auto_ack=True)
    channel.start_consuming()