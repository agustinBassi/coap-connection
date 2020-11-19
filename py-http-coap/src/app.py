###############################################################################
# Author: Agustin Bassi
# Date: November 2020
# Licence: GPLV3+
###############################################################################

#########[ Imports ]########################################################### 

import os
import json
import time
import logging
# import requests

from flask import Flask, Response, abort, json, jsonify, request, url_for
from flask_cors import CORS

#########[ Settings & Data ]###################################################

APP_CONFIG = {
    "HOST"   : "0.0.0.0",
    "PORT"   : 5100,
    "PREFIX" : "/api/v1/",
    "DEBUG"  : True,
}
# Flask App object
app = Flask(__name__)
CORS(app)
# Settings that will be modified by the user
module_data = {}

#########[ Utils ]#############################################################

def create_json_response(response, status_code):
    """
    Custom Response Function
    """
    return Response(
        mimetype="application/json",
        response=json.dumps(response),
        status=status_code
    )

def make_resource_url(resource, protocol="http", host="localhost", port=APP_CONFIG["PORT"]):
    res_url = url_for(resource)
    return f"http://localhost:{port}{res_url}"


#########[ Application Views (endpoints) ]#####################################

@app.route(APP_CONFIG["PREFIX"], methods=['GET'])
def show_resources():
    # execute local call to filter the desired fields to show
    response = {
        'http_to_coap' : {
            'url_post' : make_resource_url('execute_coap_request'),
            'url_put'  : make_resource_url('execute_coap_request'),
        },
    }
    # return the response with the status code
    return create_json_response(response, 200)

@app.route(APP_CONFIG["PREFIX"] + '/http_to_coap/', methods=['PUT', 'POST'])
def execute_coap_request():
    if not request.json:
        return create_json_response(
            {'error' : 'Impossible to parse request body'}, 
            422
            )
    # Send new current module data as response
    response = {
        "message" : "ok"
    }
    return create_json_response(response, 200)

#########[ Specific module code ]##############################################


#########[ Module main code ]##################################################

def init_app():
    pass

if __name__ == '__main__':
    init_app()
    app.run(
        host=APP_CONFIG.get("HOST"), 
        port=APP_CONFIG.get("PORT"),
        debug=APP_CONFIG.get("DEBUG"),
        )

#########[ Enf of file ]#######################################################