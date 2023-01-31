from flask import Flask, jsonify
import time
import math
import random
import os
 
# This is super hacky and we would never do this in produdction but it's for a takehome
global START_TIME 
START_TIME = time.time()
global HEAD 
HEAD = 0
global TOTAL_BLOCKS
TOTAL_BLOCKS = 0
global BLOCK_MAPPING
BLOCK_MAPPING = {}


app = Flask(__name__)
 
@app.route('/block/<int:number>', methods = ['GET'])
def block(number):
    global TOTAL_BLOCKS
    global HEAD
    if number > HEAD:
        return jsonify({'error': f'head is {HEAD} but requested number {number} is greater than it'})
    if number not in BLOCK_MAPPING:
        return jsonify({'error': f'Requested number {number} is not in BLOCK_MAPPING'})

    return jsonify({
        'time': time.time(), 
        'block': number,
        'data': f"message_{BLOCK_MAPPING[number]}"
    })


@app.route('/head', methods = ['GET'])
def head():
    global TOTAL_BLOCKS
    global HEAD
    reorg = random.random() < 0.3
    TOTAL_BLOCKS += 1
    if reorg and HEAD > 5:
        BLOCK_MAPPING.pop(HEAD)
        BLOCK_MAPPING.pop(HEAD-1)
        HEAD -= 2
    else:
        HEAD += 1
    
    BLOCK_MAPPING[HEAD] = TOTAL_BLOCKS

    return jsonify({
        'time': time.time(), 
        'head': HEAD
    })

@app.route('/all', methods = ['GET'])
def all():
    return jsonify(BLOCK_MAPPING)

if __name__ == '__main__':
 
    # run() method of Flask class runs the application
    # on the local development server.
    app.run(host=os.environ.get('FLASK_RUN_HOST', "localhost"), port=8000, debug=True)