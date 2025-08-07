# run.py
import eventlet
# This is the critical line to make `subprocess` compatible with eventlet.
eventlet.monkey_patch() 

from app import create_app, socketio

app = create_app()

if __name__ == "__main__":
    #eventlet.wsgi is automatically used when socketio.run is called with eventlet
    socketio.run(app, host="127.0.0.1", port=5000, debug=True)
