function load() {
    var newD = document.createElement('div');
    newD.className = 'container';
    document.body.appendChild(newD);
    var newP = document.createElement('p');
    newP.className = 'mcp';
    document.body.appendChild(newP);
    console.log('mcp html loaded');
};
load();

function get_params(name, parent) {
    const urlString = location.origin + parent;
    const url = new URL(urlString);
    const params = new URLSearchParams(url.search);
    return params.get(name);
}

// sse url
var url = get_params('url', window.location.search);
// sse ws 端口
var mcp_session_url = '';
// html上显示请求响应日志的自增序号
var num = 0;
// mcp 接口唯一标识
var index = 0;
// sse时,调用工具集合
var tools_calls = {};
// mcp streamable-http地址
var mcp_href = null;
// mcp streamable-http 附加头
var mcp_headers_extra = {};

function get_index() {
    index++;
    return index;
}

var mcp = new URL(url)

async function mcp_streamable_http() {
    mcp_href = location.href;
    var json7 = {
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {
                "name": "llm-logs-analysis",
                "version": "v0.1.2"
            }
        },
        "jsonrpc": "2.0",
        "id": get_index()
    };
    console.log('json7', json7);
    var res = await sendSseMessage(json7);
    var headers = res.headers;
    var data = res.data;
    var json8 = {
        "method": "notifications/initialized",
        "jsonrpc": "2.0"
    };
    console.log('json8', json8);
    if (headers.get('mcp-session-id') != null) {
        mcp_headers_extra = {
            'mcp-session-id': headers.get('mcp-session-id')
        }
    }
    await sendSseMessage(json8);
    var json9 = {
        "method": "tools/list",
        "jsonrpc": "2.0",
        "id": get_index()
    };
    console.log('json9', json9);
    await sendSseMessage(json9, async function (headers, data) {
        for (const tool of data.result.tools) {
            await show_tool_2_html(tool, false);
        }
    });
    var json10 = {
        "method": "prompts/list",
        "jsonrpc": "2.0",
        "id": get_index()
    };
    console.log('json10', json10);
    await sendSseMessage(json10, async function (headers, data) {

    });
    var json11 = {
        "method": "resources/list",
        "jsonrpc": "2.0",
        "id": get_index()
    };
    console.log('json11', json11);
    await sendSseMessage(json11, async function (headers, data) {

    });
}

if (url == null || !(mcp.pathname.endsWith('/sse') || mcp.pathname.endsWith('/mcp'))) {
    alert("url is null");
} else if (mcp.pathname.endsWith('/mcp')) {
    mcp_streamable_http();
} else if (mcp.pathname.endsWith('/sse')) {
    const sse_WebSocket = new WebSocket('ws://localhost:' + ws_port + '/sse_ws?url=' + url);
    window.sse_WebSocket = sse_WebSocket;
    sse_WebSocket.onopen = () => {
        show_step('request', url);
        console.log('sse_WebSocket:Connected to WebSocket server');
    };
    sse_WebSocket.onmessage = async (event) => {
        var json = isValidJSON(event.data);
        if (json) {
            if (json['event'] == 'ping') {
                return;
            }
            console.log('sse_WebSocket', event.data);
            show_step('response', event.data);
            if (json['event'] == 'endpoint') {
                mcp_session_url = (new URL(url)).origin + json['data'];
                var json1 = {
                    "url": mcp_session_url,
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
                            "version": "v0.1.2"
                        }
                    },
                    "jsonrpc": "2.0",
                    "id": get_index()
                };
                console.log('json1', json1);
                await sendSseMessage(json1);
            } else {
                var json = JSON.parse(json['data']);
                if (json['result']['protocolVersion']) {
                    var json2 = {
                        "url": mcp_session_url,
                        "jsonrpc": "2.0",
                        "method": "notifications/initialized"
                    };
                    console.log('json2', json2);
                    await sendSseMessage(json2, async function () {
                        if (json['result']['capabilities']['tools']) {
                            await next_step('tools');
                        }
                        if (json['result']['capabilities']['prompts']) {
                            await next_step('prompts');
                        }
                        if (json['result']['capabilities']['resources']) {
                            await next_step('resources');
                        }
                    });
                } else if (json['result']['tools']) {
                    await show_result('tools', json);
                } else if (json['result']['content']) {
                    var func = tools_calls[json['id']];
                    console.log('tools_calls', tools_calls, json['id'], func);
                    if (func != null) {
                        func();
                    }
                    if (json['result']['content'][0]['type'] == 'text') {
                        alert('result is:' + json['result']['content'][0]['text']);
                    }
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
    document.querySelector('.mcp').innerHTML += html;
}

async function next_step(type) {
    if (type == 'tools') {
        var ii = get_index();
        var json3 = {
            "url": mcp_session_url,
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
        await sendSseMessage(json3);
    } else if (type == 'prompts') {
        var ii = get_index();
        var json4 = {
            "url": mcp_session_url,
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
        await sendSseMessage(json4);
    } else if (type == 'resources') {
        var ii = get_index();
        var json5 = {
            "url": mcp_session_url,
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
        await sendSseMessage(json5);
    }
}

async function show_tool_2_html(tool, sse) {
    const toolsContainer = document.querySelector('.container');
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
    // 调用工具按钮点击事件
    button.addEventListener("click", async function () {
        var container = button.parentElement;
        var inputs = container.querySelectorAll("input");
        var inputData = {};
        inputs.forEach(function (input) {
            console.log(input.className, input.value);
            var value = input.value;
            if (input.getAttribute('ttype') == 'number') {
                value = Number(input.value);
            }
            inputData[input.className] = value;
        });
        var jsonData = JSON.stringify(inputData);
        console.log('jsonData', jsonData);
        var ii = get_index();
        var json6 = {
            "jsonrpc": "2.0",
            "id": ii,
            "url": mcp_session_url,
            "method": "tools/call",
            "params": {
                "_meta": {
                    "progressToken": ii
                },
                "name": button.role,
                "arguments": inputData
            }
        }
        var tool_timer_time = 0;
        var tool_timer = setInterval(function () {
            tool_timer_time++;
            button.textContent = tool_timer_time;
        }, 1000);
        tools_calls[ii] = function (data) {
            button.textContent = "test";
            clearInterval(tool_timer);
        }
        console.log('json6', json6);
        await sendSseMessage(json6, function (headers, json) {
            if (sse == false) {
                var func = tools_calls[json['id']];
                console.log('tools_calls', tools_calls, json['id'], func);
                if (func != null) {
                    func();
                }
                if (json['result']) {
                    if (json['result']['content'][0]['type'] == 'text') {
                        alert('result is:' + json['result']['content'][0]['text']);
                    }
                } else {
                    alert('result is:' + json['params']['data']);
                }
            }
        });
    });
    toolDiv.appendChild(button);
    var propertie_index = 0;
    var properties = tool.inputSchema.properties;
    Object.keys(properties).forEach(function (propertie) {
        const span = document.createElement('span');
        propertie_index++;
        var required = tool.inputSchema.required.includes(propertie);
        console.log(propertie, required);
        var required_span = '';
        if (required) {
            required_span = "<span style='color:red;'>*</span>";
        }
        span.innerHTML = "  " + propertie_index + "、 " + propertie + ":" + required_span + " ";
        toolDiv.appendChild(span);

        var toolInput = document.createElement('input');
        // html 控件类型
        if (properties[propertie].type == 'number') {
            toolInput.type = 'number';
        } else {
            toolInput.type = 'input';
        }

        toolInput.className = propertie;
        toolInput.setAttribute('ttype', properties[propertie].type);
        if (properties[propertie].description) {
            toolInput.setAttribute('placeholder', properties[propertie].description);
        }
        toolDiv.appendChild(toolInput);
    });

    toolsContainer.appendChild(toolDiv);
}

async function show_result(type, data) {
    var jsonData = data;
    console.log('show_result+' + type + ":", jsonData);
    if (type == 'tools') {
        for (const tool of jsonData.result.tools) {
            await show_tool_2_html(tool, true);
        }
    }
}

async function sendSseMessage(jsonData, func) {
    show_step('request', jsonData);
    var url = '/mcp_msg';
    if (mcp_href != null) {
        url = mcp_href;
    }
    headers = {
        'Content-Type': 'application/json'
    };
    const mergedHeaders = Object.assign({}, headers, mcp_headers_extra);
    return await fetch(url, {
            method: 'POST',
            headers: mergedHeaders,
            body: JSON.stringify(jsonData)
        })
        .then(response => {
            if (!response.ok) {
                // 如果响应状态不为 2xx，抛出异常
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const headers = response.headers;
            return response.text().then(data => ({
                headers: headers,
                data: data
            }));
        })
        .then(({
            headers,
            data
        }) => {
            // 若是json就转成json对象
            if (isValidJSON(data)) {
                data = JSON.parse(data);
            }
            show_step('response', data);
            console.log('Success:', data);
            if (func) {
                func(headers, data);
            }
            return {
                headers: headers,
                data: data
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
}