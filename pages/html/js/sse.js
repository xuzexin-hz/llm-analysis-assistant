document.addEventListener('DOMContentLoaded', function () {
    var newD = document.createElement('div');
    newD.className = 'container';
    document.body.appendChild(newD);
    var newP = document.createElement('p');
    newP.className = 'sse';
    document.body.appendChild(newP);
});

function get_params(name, parent) {
    const urlString = location.origin + parent;
    const url = new URL(urlString);
    const params = new URLSearchParams(url.search);
    return params.get(name);
}

// sse url
var url = get_params('url', window.location.search);
// 显示请求响应日志的自增序号
var num = 0;
// sse 接口唯一标识
var index = 0;
// 工具调用时间显示集合
var tools_calls = {};

function get_index() {
    index++;
    return index;
}

if (url == null || !url.endsWith('/sse')) {
    alert("url is null");
} else {
    const sse_WebSocket = new WebSocket('ws://localhost:' + ws_port + '/sse_ws?url=' + url);
    window.sse_WebSocket = sse_WebSocket;
    sse_WebSocket.onopen = () => {
        show_step('request', url);
        console.log('sse_WebSocket:Connected to WebSocket server');
    };
    sse_WebSocket.onmessage = (event) => {
        console.log('sse_WebSocket', event.data);
        var json = isValidJSON(event.data);
        if (json) {
            if (json['event'] == 'ping') {
                return;
            }
            show_step('response', event.data);
            if (json['event'] == 'endpoint') {
                var session_id = get_params('session_id', json['data']);
                window.session_id = session_id;
                var json1 = {
                    "url": url,
                    "session_id": window.session_id,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-03-26",
                        "capabilities": {
                            "sampling": {},
                            "roots": {
                                "listChanged": true
                            }
                        },
                        "clientInfo": {
                            "name": "llm-logs-analysis",
                            "version": "0.1.0"
                        }
                    },
                    "jsonrpc": "2.0",
                    "id": get_index()
                };
                console.log('json1', json1);
                sendSseMessage(json1);
            } else {
                var json = JSON.parse(json['data']);
                if (json['result']['protocolVersion']) {
                    var json2 = {
                        "url": url,
                        "session_id": window.session_id,
                        "jsonrpc": "2.0",
                        "method": "notifications/initialized"
                    };
                    console.log('json2', json2);
                    sendSseMessage(json2, function () {
                        if (json['result']['capabilities']['tools']) {
                            next_step('tools');
                        }
                        if (json['result']['capabilities']['prompts']) {
                            next_step('prompts');
                        }
                        if (json['result']['capabilities']['resources']) {
                            next_step('resources');
                        }
                    });
                } else if (json['result']['tools']) {
                    show_result('tools', json);
                } else if (json['result']['content']) {
                    var func = tools_calls[json['id']];
                    console.log('tools_calls', tools_calls, json['id'], func);
                    if (func != null) {
                        func();
                    }
                    alert('result is:' + json['result']['content'][0]['text']);
                }
            }
        }
    };
    sse_WebSocket.onclose = () => {
        console.log('sse_WebSocket:Disconnected from WebSocket server');
        var b = confirm('Connection closed, do you want to refresh the page');
        if (b) {
            location.reload()
        }
    };
}

function isValidJSON(obj) {
    try {
        if (obj && typeof obj === 'object' && !Array.isArray(obj)) {
            return obj;
        }
        return JSON.parse(obj); // 如果解析成功，返回解析后的对象
    } catch (e) {
        return false; // 如果出现错误，返回 false
    }
}

function show_step(t, data) {
    num = num + 1;
    console.log('show_step+' + t + ":", data);
    var json = isValidJSON(data);
    var html = '';
    var style = '';
    if (t == 'request') {
        style = 'color: blue;';
    } else {
        style = 'color: green;';
    }
    var formattedJson = '';
    if (json) {
        if (json['data'] != undefined && typeof json['data'] === 'string') {
            if (isValidJSON(json['data'])) {
                var jj = JSON.parse(json['data']);
                json['data'] = jj;
            }
        }
        console.log('show_step2', json);
        formattedJson = JSON.stringify(json, null, 2);
    } else {
        formattedJson = data;
    }
    html = num + "、   ---" + t + ":" + '<pre class="jsonContainer" style="' + style + '">' + formattedJson + '</pre>' +
        '<br/>';
    document.querySelector('.sse').innerHTML += html;
}

function next_step(type) {
    if (type == 'tools') {
        var ii = get_index();
        var json3 = {
            "url": url,
            "session_id": window.session_id,
            "method": "tools/list",
            "params": {
                "_meta": {
                    "progressToken": ii
                }
            },
            "jsonrpc": "2.0",
            "id": ii
        }
        console.log('json3', json3);
        sendSseMessage(json3);
    } else if (type == 'prompts') {
        var ii = get_index();
        var json4 = {
            "url": url,
            "session_id": window.session_id,
            "method": "prompts/list",
            "params": {
                "_meta": {
                    "progressToken": ii
                }
            },
            "jsonrpc": "2.0",
            "id": ii
        }
        console.log('json4', json4);
        sendSseMessage(json4);
    } else if (type == 'resources') {
        var ii = get_index();
        var json5 = {
            "url": url,
            "session_id": window.session_id,
            "method": "resources/list",
            "params": {
                "_meta": {
                    "progressToken": ii
                }
            },
            "jsonrpc": "2.0",
            "id": ii
        }
        console.log('json5', json5);
        sendSseMessage(json5);
    }
}

function show_result(type, data) {
    const toolsContainer = document.querySelector('.container');
    var jsonData = data;
    console.log('show_result+' + type + ":", jsonData);
    if (type == 'tools') {
        jsonData.result.tools.forEach(tool => {
            const toolDiv = document.createElement('div');

            const toolName = document.createElement('h2');
            toolName.textContent = tool.name;
            toolDiv.appendChild(toolName);

            const toolDescription = document.createElement('p');
            toolDescription.textContent = tool.description;
            toolDiv.appendChild(toolDescription);

            var button = document.createElement("button");
            button.textContent = "test";
            button.role = tool.name;
            button.addEventListener("click", function () {
                var container = button.parentElement;
                var inputs = container.querySelectorAll("input");
                var inputData = {};
                inputs.forEach(function (input) {
                    console.log(input.className, input.value);
                    inputData[input.className] = input.value;
                });
                var jsonData = JSON.stringify(inputData);
                console.log('jsonData', jsonData);
                var ii = get_index();
                var json6 = {
                    "jsonrpc": "2.0",
                    "id": ii,
                    "url": url,
                    "session_id": window.session_id,
                    "method": "tools/call",
                    "params": {
                        "_meta": {"progressToken": ii},
                        "name": button.role,
                        "arguments": inputData
                    }
                }
                console.log('json6', json6);
                sendSseMessage(json6);
                var tool_timer_time = 0;
                var tool_timer = setInterval(function () {
                    tool_timer_time++;
                    button.textContent = tool_timer_time;
                }, 1000);
                tools_calls[ii] = function (data) {
                    button.textContent = "test";
                    clearInterval(tool_timer);
                }
            });
            toolDiv.appendChild(button);
            var element_index = 0;
            for (element in tool.inputSchema.properties) {
                const span = document.createElement('span');
                element_index++;
                span.textContent = "  " + element_index + "、 " + element + ": ";
                toolDiv.appendChild(span);

                const toolInput = document.createElement('input');
                toolInput.type = 'input';
                toolInput.className = element;
                toolDiv.appendChild(toolInput);
            }

            toolsContainer.appendChild(toolDiv);
        });
    }
}

function sendSseMessage(jsonData, func) {
    show_step('request', jsonData);
    const url = '/logs_ws_msg';
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(jsonData)
    })
        .then(response => {
            if (!response.ok) {
                // 如果响应状态不为 2xx，抛出异常
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            show_step('response', data);
            console.log('Success:', data);
            if (func) {
                func();
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
}