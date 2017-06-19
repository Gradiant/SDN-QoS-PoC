# Proof of Concept de la aplicación de QoS en redes SDN

Este código permite utilizar el emulador de redes mininet para comprobar la aplicación de QoS a flujos a través de las queue de OpenFlow 1.3

## Instrucciones

Necesitamos tener instalado mininet, con las modificaciones realizadas para permitir el uso de TCLinks (enlaces donde configuramos su ancho de banda y/o retardo) con openvswitch-qos. La version original de mininet no permite este uso simultaneo.

Para ello:

```
cd mininet
./util install -n
``` 

Necesitamos un video con un codec que permita su streaming. Actualmente utilizamos el video de big buck bunny MP4+H264 FullHD.

Lanzamos la tipología mininet con:

```
sudo python upgrade_QoS.py 
```

Este comando abre tres terminales y dos clientes vlc.

Ejecutaremos en el terminal "RTP Stream Emiter":

```
./send_video.sh PATH_TO_VIDEO_FILE
```

Deberemos comenzar a ver el video en ambos clientes vlc, tanto el premium user como el regular user.

Generamos un flujo de datos udp de 2 minutos y 5Mbps desde el terminal Udp Noise Sender al terminal UDP Noise Receiver mediante:

```
iperf -u -c 10.0.0.5 -b 5M -t 120
```

Comprobamos que solo el usuario regular, que comparte la cola del router Core2 con este flujo udp se ve afectado.

Podemos de forma dinamica reasignar el usuario a la cola prioritaria mediante reglas OpenFlow, generadas por el script set_priority

```
./set_priority.sh 10.0.0.1 10.0.0.4 hi
```

Podemos reasignar al usuario de nuevo a la cola regular con:

```
./set_priority.sh 10.0.0.1 10.0.0.4 lo
```

para salir de la prueba de concepto basta ejecutar exit en la consola de mininet.

