#!/usr/bin/env python

import eventlet
eventlet.monkey_patch()

import os
import json
from flask import Flask
from flask_socketio import SocketIO

import supcast.config
import supcast.supcredis

import logging
logger = logging.getLogger()

app = Flask('supcast.wsapp')
app.config['SECRET_KEY'] = 'TODO: some secret?'
socketio = SocketIO(app, async_mode='eventlet')

def redis_listener():
    r = supcast.supcredis.server()
    ps = r.pubsub()
    ps.subscribe('process')
    for msg in ps.listen():
        if msg['type'] != 'message':
            continue
        try:
            socketio.emit('process',
                          json.loads(msg['data'].decode('utf8')),
                          namespace='/ws')
        except:
            logger.exception('error sending')

eventlet.spawn(redis_listener)

def setup_app():
    redis_url = os.environ['REDIS_URL']
    supcast.config.set_redis_url(redis_url)

setup_app()

@app.route('/')
def index():
    return index_html

@socketio.on('connect', namespace='/ws')
def ws_connect():
    logger.info("someone connected")


@socketio.on('disconnect', namespace='/ws')
def ws_disconnect():
    logger.info("someone disconnected")


index_html = """
<!DOCTYPE HTML>
<html>
<head>
    <title>Flask-SocketIO Test</title>
    <script type="text/javascript" src="//code.jquery.com/jquery-1.4.2.min.js"></script>
    <script type="text/javascript" src="//cdnjs.cloudflare.com/ajax/libs/socket.io/1.3.5/socket.io.min.js"></script>
    <script type="text/javascript" charset="utf-8">
        $(document).ready(function(){
            namespace = '/ws'; // change to an empty string to use the global namespace

            // the socket.io documentation recommends sending an explicit package upon connection
            // this is specially important when using the global namespace
            var socket = io.connect('http://' + document.domain + ':' + location.port + namespace);

            // event handler for server sent data
            // the data is displayed in the "Received" section of the page
            socket.on('process', function(msg) {
                console.log(msg);
                $('#log').append('<br>Received ' + msg);
            });

            // event handler for new connections
            socket.on('connect', function() {
                socket.emit('my event', {data: 'I am connected!'});
            });
        });
    </script>
</head>
<body>
    <h1>Flask-SocketIO Test</h1>
    <h2>Receive:</h2>
    <div id="log"></div>
</body>
</html>
"""

if __name__ == '__main__':
    socketio.run(app, debug=True)

