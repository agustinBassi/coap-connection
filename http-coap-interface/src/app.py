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
# CORS policy to act over Flask object
CORS(app)


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
        'http_to_coap_test' : {
            'url_post' : make_resource_url('test_coap_request'),
            'url_put'  : make_resource_url('test_coap_request'),
        },
    }
    # return the response with the status code
    return create_json_response(response, 200)


@app.route(APP_CONFIG["PREFIX"] + '/http_to_coap/test/', methods=['PUT', 'POST'])
def test_coap_request():
    if not request.json:
        response = generate_invalid_coap_response()
        return create_json_response(response, 422)
    coap_fields = create_coap_fields_from_http_request(**request.json)
    command_response = generate_test_coap_response(**coap_fields)
    return create_json_response(command_response, 200)


@app.route(APP_CONFIG["PREFIX"] + '/http_to_coap/', methods=['PUT', 'POST'])
def execute_coap_request():
    if not request.json:
        response = generate_invalid_coap_response()
        return create_json_response(response, 422)
    coap_fields = create_coap_fields_from_http_request(**request.json)
    command_response = execute_coap_client_request(**coap_fields)
    return create_json_response(command_response, 200)


#########[ Specific module code ]##############################################


def generate_invalid_coap_response(**kwargs):
    return {
        "error" : "invalid data received from client",
        "received" : kwargs,
        "solution" : "pass correct message request body in JSON format",
        "request_body_example": {
            "coap_server_ip" : "192.168.1.37",
            "coap_server_resource" : "light",
            "coap_server_port" : 5683,
            "coap_method" : "put",
            "coap_payload" : {
                "light": False
            }
        }
    }


def create_coap_fields_from_http_request(**kwargs):
    return {
        "coap_server_ip" : kwargs.get("coap_server_ip", "INVALID"),
        "coap_server_resource" : kwargs.get("coap_server_resource", "INVALID"),
        "coap_server_port" : int(kwargs.get("coap_server_port", 0)),
        "coap_method" : kwargs.get("coap_method", "INVALID").lower(),
        "coap_payload" : kwargs.get("coap_payload", {}),
    }


def generate_test_coap_response(**kwargs):
    return {
        "message" : "Test HTTP-COAP Interface endpoint",
        "received" : kwargs,
    }


def parse_coap_client_response(command_output):
    
    def _process_status_message(message):
        coap_status_message = {
            "2.00" : "OK",
            "2.01" : "Created",
            "2.02" : "Deleted",
            "2.03" : "Valid",
            "2.04" : "Changed",
            "2.05" : "Content",
            "2.31" : "Continue",
            "4.0"  : "Bad Request",
            "4.01" : "Unauthorized",
            "4.02" : "Bad Option",
            "4.03" : "Forbidden",
            "4.04" : "Not Found",
            "4.05" : "Method Not Allowed",
            "4.06" : "Not Acceptable",
            "4.08" : "Request Entity Incomplt.",
            "4.12" : "Precondition Failed",
            "4.13" : "Request Ent. Too Large",
            "4.15" : "Unsupported Content-Fmt.",
            "5.00" : "Internal Server Error",
            "5.01" : "Not Implemented",
            "5.02" : "Bad Gateway",
            "5.03" : "Service Unavailable",
            "5.04" : "Gateway Timeout",
            "5.05" : "Proxying Not Supported",
        }
        status_response = {
            "coap_status_response": message,
            "coap_status_description": coap_status_message.get(message, "")
        }
        return status_response
        
    splitted = command_output.split("\n")
    try:
        message_output = json.loads(splitted[1])
        if isinstance(message_output, (int, float)):
            message_output = _process_status_message(str(message_output))
    except:
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
        "message_id": f"0x{message_id}",
        "output" : message_output,
    }


def execute_coap_client_request(**kwargs):

    def _validate_fields():
        if kwargs.get('coap_server_ip') == "INVALID":
            return False
        if kwargs.get('coap_server_resource') == "INVALID":
            return False
        if kwargs.get('coap_server_port') == 0:
            return False
        if kwargs.get('coap_method') == "INVALID":
            return False
        if kwargs.get('coap_method') in ["put", "post"]:
            if not kwargs.get('coap_payload'):
                return False
        return True

    def _create_get_or_delete_command_list(method="get"):
        command_list = []
        command_list.append("coap-client")
        command_list.append("-m")
        command_list.append(method)
        command_list.append("-p")
        command_list.append(f"{kwargs.get('coap_server_port')}")
        connection = f"coap://{kwargs.get('coap_server_ip')}/{kwargs.get('coap_server_resource')}"
        command_list.append(connection)
        return command_list

    def _create_put_or_post_command_list(method="put"):
        command_list = []
        command_list.append("coap-client")
        command_list.append("-m")
        command_list.append(method)
        command_list.append("-e")
        payload = json.dumps(kwargs.get('coap_payload')).replace(" ", "")
        command_list.append(payload)
        command_list.append("-p")
        command_list.append(f"{kwargs.get('coap_server_port')}")
        connection = f"coap://{kwargs.get('coap_server_ip')}/{kwargs.get('coap_server_resource')}"
        command_list.append(connection)
        return command_list

    if not _validate_fields():
        return generate_invalid_coap_response(**kwargs)

    command_list = []
    if kwargs.get('coap_method') in ["get", "delete"]:
        command_list = _create_get_or_delete_command_list(method=kwargs.get('coap_method'))
    elif kwargs.get('coap_method') in ["put", "post"]:
        command_list = _create_put_or_post_command_list(method=kwargs.get('coap_method'))
    else:
        print(f"Unsupported CoAP method")
        return generate_invalid_coap_response(**kwargs)

    command_output = subprocess.Popen(
        command_list, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT
        )
    stdout, _ = command_output.communicate()
    decoded_output = stdout.decode('utf-8')
    command_response = parse_coap_client_response(decoded_output)
    return command_response


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