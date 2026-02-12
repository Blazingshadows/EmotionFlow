from flask import Flask, request
import webbrowser
import os
from spotipy.oauth2 import SpotifyOAuth

app = Flask(__name__)
auth_code = None

@app.route('/callback')
def callback():
    global auth_code
    auth_code = request.args.get('code')
    return f"Authorization successful! You can close this window."

if __name__ == '__main__':
    # Start server
    app.run(host='127.0.0.1', port=8888, debug=False)