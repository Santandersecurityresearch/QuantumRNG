import flask
from flask import request, jsonify
import base64
import json

app = flask.Flask(__name__)
# obviously, this alone makes it TOTALLY UNSUITABLE for production... NO, REALLY! -MC
app.config['DEBUG'] = True

# Run the QRNG stuff
from qrng import QuantumRNG
qrng = QuantumRNG()

"""
Although this works as a PoC - there are still a large number of things TODO - 
 * add HTTPS support (don't want anyone snooping)
 * add auth
 * do some real world testing
 * add threading for high-volume applications

Feel free to add, expand, and improvise :P -MC.
"""


@app.route('/', methods=['GET','POST'])
def home():
    return '''<h1> Welcome!</h1>
     <p>This is the prototype QuantumRNG-as-a-Service flask api...</p>
     <p><b>THIS IS  NOT FOR PRODUCTION!!</b></p>'''

# this function returns 512 random bytes Base64 encoded...
@app.route('/api/v1/qrng/get_bits', methods=['GET'])
def get_bits():
    rand_bytes = qrng.get_rand_bytes(N=512)
    output = {}
    output['512_qrng_bits'] = base64.b64encode(rand_bytes).decode('utf-8')
    return jsonify(output)

@app.route('/api/v1/qrng/get_num_bits/<num_bits>', methods=['GET'])
def get_num_bits(num_bits):
    rand_bytes = qrng.get_rand_bytes(N=int(num_bits))
    output = {}
    output['qrng_bits'] = base64.b64encode(rand_bytes).decode('utf-8')
    return jsonify(output)

app.run()