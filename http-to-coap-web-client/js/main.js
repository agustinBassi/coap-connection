/**
 * Author: Agustin Bassi
 * Date: July 2020
 * Licence: GPLv3+
 * Brief: TODO comment it
 */

//=======[ Settings & Data ]===================================================

const DEFAULT_HTTP_METHOD           = "PUT";
const DEFAULT_HTTP_TO_COAP_URL      = "http://localhost:5100/api/v1/http_to_coap/test/";
const DEFAULT_COAP_SERVER_IP        = "localhost";
const DEFAULT_COAP_SERVER_RESOURCE  = ".well-known/core";
const DEFAULT_COAP_SERVER_PORT      = 5683;
const DEFAULT_COAP_METHOD           = "get";
const DEFAULT_COAP_PAYLOAD          = {};
const DEFAULT_LOG_LINES             = 1;
const MAX_LOG_LINES                 = 10;

var HttpHandler     = new XMLHttpRequest();
var PollReqInterval = null;

//=======[ Utils ]=============================================================

function View_ShowLogData(server_response) {
    var json_response = JSON.parse(server_response);
    console.log("Data received is: " + server_response);
    document.getElementById("logs_textarea").innerHTML = server_response;
}

function View_AppendLogData(server_response) {
    current_value = document.getElementById("logs_textarea").value; 
    log_lines     = Utils_GetElementValue("log_lines");
    log_lines     = parseInt(log_lines);
    if (current_value.split("\n").length-1 >= log_lines){
        View_ClearLogData();
        current_value = "";
    } 
    document.getElementById("logs_textarea").innerHTML = server_response + "\n" + current_value;
}

function View_ClearLogData(){
    console.log("Clearing view data")
    document.getElementById("logs_textarea").innerHTML = "";
}

function Utils_LogCurrentSettings(){
    coap_server_ip            = Utils_GetElementValue("coap_server_ip");
    coap_server_resource      = Utils_GetElementValue("coap_server_resource");
    coap_server_port          = Utils_GetElementValue("coap_server_port");
    coap_method               = Utils_GetElementValue("coap_method");
    coap_payload              = Utils_GetElementValue("coap_payload");
    http_to_coap_endpoint_url = Utils_GetElementValue("http_to_coap_endpoint_url");
    log_lines                 = Utils_GetElementValue("log_lines");

    console.log("coap_server_ip:            " + coap_server_ip);
    console.log("coap_server_resource:      " + coap_server_resource);
    console.log("coap_server_port:          " + coap_server_port);
    console.log("coap_method:               " + coap_method);
    console.log("coap_payload:              " + coap_payload);
    console.log("http_to_coap_endpoint_url: " + http_to_coap_endpoint_url);
    console.log("log_lines:                 " + log_lines);
}

function Utils_GetElementValue(element_to_get){
    // TODO: Evaluate other element types like checkbox, dropdown, etc.
    return document.getElementById(element_to_get).value;
}

function Utils_IsInvalidValue(value){
    if (value == null || value == "" || value == "undefined"){
        return true;
    }
    return false;
}

function Timer_ClearPollInterval(){
    if(PollReqInterval != null){
        clearInterval(PollReqInterval);
        PollReqInterval = null;
    }
}

function Timer_IsIntervalSet(){
    return PollReqInterval != null;
}

//=======[ CoAP Management ]===================================================

function Coap_MakeRequest(){
    // set default values for each CoAP field
    let coap_server_ip   = Utils_GetElementValue("coap_server_ip");
    if (Utils_IsInvalidValue(coap_server_ip)){
        coap_server_ip = DEFAULT_COAP_SERVER_IP;
    }
    let coap_server_resource   = Utils_GetElementValue("coap_server_resource");
    if (Utils_IsInvalidValue(coap_server_resource)){
        coap_server_resource = DEFAULT_COAP_SERVER_RESOURCE;
    }
    let coap_server_port   = Utils_GetElementValue("coap_server_port");
    if (Utils_IsInvalidValue(coap_server_port)){
        coap_server_port = DEFAULT_COAP_SERVER_PORT;
    } else {
        coap_server_port = parseInt(coap_server_port);
    }
    let coap_method   = Utils_GetElementValue("coap_method");
    if (Utils_IsInvalidValue(coap_method)){
        coap_method = DEFAULT_COAP_METHOD;
    }
    let coap_payload   = Utils_GetElementValue("coap_payload");
    if (Utils_IsInvalidValue(coap_payload)){
        coap_payload = DEFAULT_COAP_PAYLOAD;
    } else {
        coap_payload = JSON.parse(coap_payload);
    }
    // create json for execute CoAP request
    let coap_request = {
        "coap_server_ip": coap_server_ip,
        "coap_server_resource": coap_server_resource,
        "coap_server_port": coap_server_port,
        "coap_method": coap_method,
        "coap_payload": coap_payload,
    }
    return JSON.stringify(coap_request);
}

//=======[ Module functions ]==================================================

function App_ExecuteHttpToCoapRequest(){
    // at first los current settings
    Utils_LogCurrentSettings();

    let request_url   = Utils_GetElementValue("http_to_coap_endpoint_url");
    if (Utils_IsInvalidValue(request_url)){
        request_url = DEFAULT_HTTP_TO_COAP_URL;
    }
    let log_lines   = Utils_GetElementValue("log_lines");
    if (Utils_IsInvalidValue(log_lines)){
        log_lines = DEFAULT_LOG_LINES;
    } else {
        log_lines = parseInt(log_lines);
    }
    let http_method = DEFAULT_HTTP_METHOD;
    let poll_checkbox = false;
    // callback when HTTP request is done
    HttpHandler.onreadystatechange = function() {
        if (this.readyState == 4 && (this.status == 200 || this.status == 201 )) {
            if (Timer_IsIntervalSet()){
                View_AppendLogData(HttpHandler.responseText);
            } else {
                View_ShowLogData(HttpHandler.responseText);
            }
        } else{
            console.log("The server has returned an error code");
        }
    };
    // clear view in order to start new log session
    View_ClearLogData();
    // clear interval if exists
    Timer_ClearPollInterval();
    // evaluate HTTP method
    if(http_method.toLowerCase() == "get"){
        HttpHandler.open("GET", request_url, true);
        HttpHandler.setRequestHeader('Accept', 'application/json');
        HttpHandler.send();
        if(poll_checkbox == true){
            console.log("Executing poll request each seconds " + poll_secs)
            poll_secs = parseInt(poll_secs);
            PollReqInterval = setInterval(function(){
                HttpHandler.open("GET", request_url, true);
                HttpHandler.setRequestHeader('Accept', 'application/json');
                HttpHandler.send();
            }, poll_secs * 1000);
        }
    } 
    else if(http_method.toLowerCase() == "post" || http_method.toLowerCase() == "put"){
        request_data = Coap_MakeRequest();
        console.log("Sending CoAP request: " + request_data);
        HttpHandler.open(http_method.toUpperCase(), request_url);
        HttpHandler.setRequestHeader('Accept', 'application/json');
        HttpHandler.setRequestHeader("Content-type", 'application/json;charset=UTF-8');
        HttpHandler.send(request_data);
    } 
    else if(http_method.toLowerCase() == "delete"){
        HttpHandler.open("DELETE", request_url, true);
        HttpHandler.send();
    } 
    else {
        console.log("Unsupported HTTP Method selected by the user")
    }
}

//=======[ End of file ]=======================================================
