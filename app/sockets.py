# app/sockets.py
from . import socketio

#def init_socketio(sio):
    #pass  # For future socket-specific setup

# app/sockets.py
def init_socketio(socketio):
    # This handler is for the default namespace.
    @socketio.on('connect')
    def handle_connect():
        print('Client connected to default namespace')

    @socketio.on('disconnect')
    def handle_disconnect():
        print('Client disconnected from default namespace')

    # Add a handler for the '/scan' namespace to ensure the server
    # is actively listening for connections on this path.
    @socketio.on('connect', namespace='/scan')
    def handle_scan_connect():
        print('Client connected to /scan namespace')
    
    @socketio.on('disconnect', namespace='/scan')
    def handle_scan_disconnect():
        print('Client disconnected from /scan namespace')


    
