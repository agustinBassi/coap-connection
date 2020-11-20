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
import subprocess
from subprocess import Popen, PIPE

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
        response = {
            "error" : "Impossible to parse request body"
        }
        return create_json_response(response, 422)
    # Send new current module data as response
    coap_fields = create_coap_fields_from_http_request(**request.json)
    command_response = execute_coap_client_request(**coap_fields)
    return create_json_response(command_response, 200)

#########[ Specific module code ]##############################################


def create_coap_fields_from_http_request(**kwargs):
    """
    coap_fields = {
        "coap_server" : "192.168.1.37",
        "coap_port" : 5683,
        "coap_resource" : "button",
        "coap_method" : "get",
    }
    """
    return {
        "coap_server" : kwargs.get("coap_server", "INVALID"),
        "coap_port" : int(kwargs.get("coap_port", 0)),
        "coap_resource" : kwargs.get("coap_resource", "INVALID"),
        "coap_method" : kwargs.get("coap_method", "INVALID").lower(),
        "coap_payload" : kwargs.get("coap_payload", {}),
    }


def execute_coap_client_request(**kwargs):
    """
    docker-compose run py-http-coap coap-client -m get -p 5683 coap://192.168.1.37/button
    """

    def _validate_fields():
        if kwargs.get('coap_server') == "INVALID":
            return False
        if kwargs.get('coap_port') == 0:
            return False
        if kwargs.get('coap_resource') == "INVALID":
            return False
        if kwargs.get('coap_method') == "invalid":
            return False
        return True

    def _create_get_command_list():
        command_list = []
        command_list.append("coap-client")
        command_list.append("-m")
        command_list.append("get")
        command_list.append("-p")
        command_list.append(f"{kwargs.get('coap_port')}")
        connection = f"coap://{kwargs.get('coap_server')}/{kwargs.get('coap_resource')}"
        command_list.append(connection)
        return command_list

    if not _validate_fields():
        return generate_invalid_coap_response(**kwargs)

    command_list = []
    if kwargs.get('coap_method') == "get":
        command_list = _create_get_command_list()
    else:
        print(f"Unsupported CoAP method")

    command_output = subprocess.Popen(
        command_list, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT
        )
    stdout, _ = command_output.communicate()
    decoded_output = stdout.decode('utf-8')
    command_response = parse_coap_client_response(decoded_output)
    return command_response


def generate_invalid_coap_response(**kwargs):
    return {
        "error" : "invalid data received from client",
        "received" : kwargs,
        "solution" : "pass correct message like: 'coap-client -m get -p 5683 coap://192.168.1.37/button'",
    }


def parse_coap_client_response(command_output):
    splitted = command_output.split("\n")
    message_output = splitted[1]
    total_info = splitted[0].split(" ")
    version = total_info[0].split(":")[1]
    message_type = total_info[1].split(":")[1]
    method = total_info[2].split(":")[1]
    message_id = total_info[3].split(":")[1]
    return {
        "version": version,
        "message_type": message_type,
        "method": method,
        "message_id": message_id,
        "output" : message_output,
    }


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