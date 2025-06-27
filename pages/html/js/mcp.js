function load() {
    var newD = document.createElement('div');
    newD.className = 'container';
    document.body.appendChild(newD);
    var newP = document.createElement('p');
    newP.className = 'mcp';
    document.body.appendChild(newP);
    console.log('mcp html loaded');

    const container = document.querySelector('.container');
    const table = document.createElement('table');
    table.className = 'container-table';
    table.style = "border-spacing: 4px 24px;";
    container.appendChild(table);
    const style = document.createElement("style");
    //按钮点击后的扫灯效果
    style.innerText =
        `
        *, *::before, *::after {
            box-sizing: border-box;
        }
        @keyframes rotate {
            100% {
                transform: rotate(1turn);
            }
        }
        .button {
            color: red;
            position: relative;
            z-index: 0;
            overflow: hidden;
            &::before {
                content:'';
                position: absolute;
                z-index: -2;
                left: -50%;
                top: -50%;
                width: 200%;
                height: 200%;
                background-color: #1a232a;
                background-repeat: no-repeat;
                background-position: 0 0;
                background-image: conic-gradient(transparent, rgba(168, 239, 255, 1), transparent 30%);
                animation: rotate 4s linear infinite;
            }
            &::after {
                content:'';
                position: absolute;
                z-index: -1;
                left: 6px;
                top: 6px;
                width: calc(100% - 1px);
                height: calc(100% - 1px);
                border-radius: 5px;
            }
        }
        .button::after {
            animation: opacityChange 5s infinite linear;
        }
        @keyframes opacityChange {
            50% {
                opacity:.5;
            }
            100% {
                opacity: 1;
            }
        }
    `;
    document.body.appendChild(style);
};

load();

// sse url
var url = getParams('url', window.location.search);
// sse ws 端口
var mcp_session_url = '';
// html上显示请求响应日志的自增序号
var num = 0;
// mcp 接口唯一标识
var index = 0;
// mcp调用集合
var mcp_calls = {};
// mcp streamable-http地址
var mcp_href = null;
// mcp streamable-http 附加头
var mcp_headers_extra = {};

function getParams(name, parent) {
    const urlString = location.origin + parent;
    const url = new URL(urlString);
    const params = new URLSearchParams(url.search);
    return params.get(name);
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

function getIndex() {
    index++;
    return index;
}

var stdio_WebSocket = null;
var stdio_step = 0;
if (url == null) {
    var stdio_command = localStorage.getItem('stdio_command');
    var command = prompt("请输入stdio的完整命令和参数(如:python -m mcp_server_fetch)", localStorage.hasOwnProperty(
        'stdio_command') ? stdio_command : "python -m mcp_server_fetch");
    if (command == null) {
        throw new Error("command is null");
    }
    localStorage.setItem('stdio_command', command);
    const container = document.querySelector('.container');
    const div = document.createElement('div');
    div.className = 'container-stdio';
    div.style = "border-spacing: 4px 24px;";
    div.style = "border: 1px dotted;color: red;";
    div.innerText = "当前Stdio命令为: " + command;
    if (container.firstChild) {
        container.insertBefore(div, container.firstChild);
    } else {
        container.appendChild(div);
    }

    stdio_WebSocket = new WebSocket('ws://localhost:' + ws_port + '/sse_ws?url=stdio&command=' + command);
    window.stdio_WebSocket = stdio_WebSocket;
    stdio_WebSocket.onopen = async () => {
        console.log('stdio_WebSocket:Connected to WebSocket server');
        await mcpStdio();
    };
    stdio_WebSocket.onmessage = async (event) => {
        var json = isValidJSON(event.data);
        showStep('response', json);
        if (!json['logger']) {
            stdio_step = stdio_step + 1;
            await mcpStdio();
        }
        if (json['result']) {
            if (json['result']['capabilities']) {
                if (json['result']['capabilities']['tools']) {
                    await mcpStdio('tools');
                }
                if (json['result']['capabilities']['prompts']) {
                    await mcpStdio('prompts');
                }
                if (json['result']['capabilities']['resources']) {
                    await mcpStdio('resources');
                }
            } else if (json['result']['tools']) {
                await showGetResult('tools', json, true);
            } else if (json['result']['prompts']) {
                await showGetResult('prompts', json, true);
            } else if (json['result']['resources']) {
                await showGetResult('resources', json, true);
                //tools调用结果
            } else if (json['result']['content']) {
                showCallResult(json, 'tools');
                //prompts调用结果
            } else if (json['result']['messages']) {
                showCallResult(json, 'prompts');
                //resources调用结果
            } else if (json['result']['contents']) {
                showCallResult(json, 'resources');
            }
        } else {
            if (json == false) {
                alert(event.data);
            }
        }
    };
    stdio_WebSocket.onclose = () => {
        console.log('stdio_WebSocket:Disconnected from WebSocket server');
        var b = confirm('Connection closed, do you want to refresh the page');
        if (b) {
            location.reload()
        }
    };
} else {
    var mcp = new URL(url);
    if (url == null || !(mcp.pathname.endsWith('/sse') || mcp.pathname.endsWith('/mcp'))) {
        alert("不符合mcp-sse或mcp-streamable-http格式");
    } else if (mcp.pathname.endsWith('/mcp')) {
        mcpStreamableHttp();
    } else if (mcp.pathname.endsWith('/sse')) {
        const sse_WebSocket = new WebSocket('ws://localhost:' + ws_port + '/sse_ws?url=' + url);
        window.sse_WebSocket = sse_WebSocket;
        sse_WebSocket.onopen = () => {
            showStep('request', url);
            console.log('sse_WebSocket:Connected to WebSocket server');
        };
        sse_WebSocket.onmessage = async (event) => {
            var json = isValidJSON(event.data);
            await mcpSSE(json);
        };
        sse_WebSocket.onclose = () => {
            console.log('sse_WebSocket:Disconnected from WebSocket server');
            var b = confirm('Connection closed, do you want to refresh the page');
            if (b) {
                location.reload()
            }
        };
    }
}

//mcp streamable-http 调用过程
async function mcpStreamableHttp() {
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
        "id": getIndex()
    };
    console.log('json7', json7);
    var json = {};
    var res = await sendSseMessage(json7, function (headers, data) {
        json = data;
    });
    console.log('json', json);
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
    if (json['result']['capabilities']) {
        if (json['result']['capabilities']['tools']) {
            var ii = getIndex();
            var json9 = {
                "method": "tools/list",
                "params": {
                    "_meta": {
                        "progressToken": ii
                    }
                },
                "jsonrpc": "2.0",
                "id": ii
            };
            console.log('json9', json9);
            await sendSseMessage(json9, async function (headers, data) {
                showGetResult("tools", data, false);
            });
        }
        if (json['result']['capabilities']['prompts']) {
            var ii = getIndex();
            var json10 = {
                "method": "prompts/list",
                "params": {
                    "_meta": {
                        "progressToken": ii
                    }
                },
                "jsonrpc": "2.0",
                "id": ii
            };
            console.log('json10', json10);
            await sendSseMessage(json10, async function (headers, data) {
                showGetResult("prompts", data, false);
            });
        }
        if (json['result']['capabilities']['resources']) {
            var ii = getIndex();
            var json11 = {
                "method": "resources/list",
                "params": {
                    "_meta": {
                        "progressToken": ii
                    }
                },
                "jsonrpc": "2.0",
                "id": ii
            };
            console.log('json11', json11);
            await sendSseMessage(json11, async function (headers, data) {
                showGetResult("resources", data, false);
            });
        }
    }
}

async function toStdioMsg(json, new_timeout) {
    showStep('request', json);
    var timeout = 0;
    if (new_timeout) {
        timeout = new_timeout;
    }
    stdio_WebSocket.send(JSON.stringify(json));
    return new Promise(function (resolve, reject) {
        console.log('toStdioMsg', json);
        setTimeout(function () {
            console.log('ok', json);
            resolve();
        }, timeout);
    });
}

//mcp stdio 调用过程
async function mcpStdio(type) {
    console.log('stdio_step', stdio_step);
    if (type == 'tools') {
        var ii = getIndex();
        var json9 = {
            "method": "tools/list",
            "params": {
                "_meta": {
                    "progressToken": ii
                }
            },
            "jsonrpc": "2.0",
            "id": ii
        };
        console.log('json9', json9);
        await toStdioMsg(json9, 200);
    } else if (type == 'prompts') {
        var ii = getIndex();
        var json10 = {
            "method": "prompts/list",
            "params": {
                "_meta": {
                    "progressToken": ii
                }
            },
            "jsonrpc": "2.0",
            "id": ii
        };
        console.log('json10', json10);
        await toStdioMsg(json10, 200);
    } else if (type == 'resources') {
        var ii = getIndex();
        var json11 = {
            "method": "resources/list",
            "params": {
                "_meta": {
                    "progressToken": ii
                }
            },
            "jsonrpc": "2.0",
            "id": ii
        };
        console.log('json11', json11);
        await toStdioMsg(json11, 200);
    } else if (stdio_step == 0) {
        var json7 = {
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
            "id": getIndex()
        };
        console.log('json7', json7);
        await toStdioMsg(json7);
    } else if (stdio_step == 1) {
        var json8 = {
            "method": "notifications/initialized",
            "jsonrpc": "2.0"
        };
        console.log('json8', json8);
        await toStdioMsg(json8);
    }
}

//mcp sse 调用过程
async function mcpSSE(json) {
    if (json) {
        console.log('sse_WebSocket', event.data);
        showStep('response', event.data);
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
                "id": getIndex()
            };
            console.log('json1', json1);
            await sendSseMessage(json1);
        } else {
            var json = JSON.parse(json['data']);
            if (json['result']) {
                if (json['result']['protocolVersion']) {
                    var json2 = {
                        "url": mcp_session_url,
                        "jsonrpc": "2.0",
                        "method": "notifications/initialized"
                    };
                    console.log('json2', json2);
                    await sendSseMessage(json2, async function () {
                        if (json['result']['capabilities']['tools']) {
                            await nextStep('tools');
                        }
                        if (json['result']['capabilities']['prompts']) {
                            await nextStep('prompts');
                        }
                        if (json['result']['capabilities']['resources']) {
                            await nextStep('resources');
                        }
                    });
                } else if (json['result']['tools']) {
                    await showGetResult('tools', json, true);
                } else if (json['result']['prompts']) {
                    await showGetResult('prompts', json, true);
                } else if (json['result']['resources']) {
                    await showGetResult('resources', json, true);
                    //tools调用结果
                } else if (json['result']['content']) {
                    showCallResult(json, 'tools');
                    //prompts调用结果
                } else if (json['result']['messages']) {
                    showCallResult(json, 'prompts');
                    //resources调用结果
                } else if (json['result']['contents']) {
                    showCallResult(json, 'resources');
                }
            } else {
                if (json == false) {
                    alert(event.data);
                }
            }
        }
    }
}

//显示请求日志
function showStep(t, data) {
    num = num + 1;
    console.log('showStep+' + t + ":", data);
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
        console.log('showStep2', json);
        formattedJson = JSON.stringify(json, null, 2);
    } else {
        formattedJson = data;
    }
    html = num + "、   ---" + t + ":" + '<pre class="jsonContainer" style="' + style + '">' + formattedJson + '</pre>' +
        '<br/>';
    document.querySelector('.mcp').innerHTML += html;
}

async function nextStep(type) {
    if (type == 'tools') {
        var ii = getIndex();
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
        var ii = getIndex();
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
        var ii = getIndex();
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

//显示获取结果
async function showGetResult(type, data, sse) {
    var jsonData = data;
    console.log('showGetResult+' + type + ":", jsonData);
    if (type == 'tools') {
        mcp2html(type);
        for (const tool of jsonData.result.tools) {
            await showItem2Html(type, tool, sse);
        }
    } else if (type == 'prompts') {
        mcp2html(type);
        for (const tool of jsonData.result.prompts) {
            await showItem2Html(type, tool, sse);
        }
    } else if (type == 'resources') {
        mcp2html(type);
        for (const resource of jsonData.result.resources) {
            await showItem2Html(type, resource, sse);
        }
    }
}

//html方式显示类别
function mcp2html(type) {
    const table = document.querySelector('.container-table');
    const tr = document.createElement('tr');
    const td1 = document.createElement('td');
    const td2 = document.createElement('td');
    td1.style = "border: 1px dotted;";
    if (type == 'tools') {
        td1.innerHTML = "Tool集合";
        td2.className = "tools";

    } else if (type == 'prompts') {
        td1.innerHTML = "prompt集合";
        td2.className = "prompts";
    } else if (type == 'resources') {
        td1.innerHTML = "resource集合";
        td2.className = "resources";
    }
    td2.style = "padding-left: 28px;";
    tr.appendChild(td1);
    tr.appendChild(td2);
    table.appendChild(tr);
}

//html方式显示单个
async function showItem2Html(type, item, sse) {
    const containerTd = document.querySelector('.' + type);
    const itemDiv = document.createElement('div');
    const itemName = document.createElement('h2');
    itemName.textContent = item.name;
    itemDiv.appendChild(itemName);

    const itemDescription = document.createElement('p');
    itemDescription.textContent = item.description;
    itemDiv.appendChild(itemDescription);

    var button = document.createElement("button");
    button.textContent = "test";
    button.role = item.name;
    button.style = "width:36px;height:25px;";
    // 调用工具按钮点击事件
    button.addEventListener("click", async function () {
        button.className = "button";
        button.textContent = "0";
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
        var json6 = null;
        var ii = getIndex();
        if (type == "tools") {
            json6 = {
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
        } else if (type == "prompts") {
            json6 = {
                "jsonrpc": "2.0",
                "id": ii,
                "url": mcp_session_url,
                "method": "prompts/get",
                "params": {
                    "_meta": {
                        "progressToken": ii
                    },
                    "name": button.role,
                    "arguments": inputData
                }
            }
        } else if (type == "resources") {
            json6 = {
                "jsonrpc": "2.0",
                "id": ii,
                "url": mcp_session_url,
                "method": "resources/read",
                "params": inputData
            }
        }

        var item_timer_time = 0;
        var item_timer = setInterval(function () {
            item_timer_time++;
            button.textContent = item_timer_time;
        }, 1000);
        mcp_calls[ii] = function () {
            button.textContent = "test";
            button.className = "";
            clearInterval(item_timer);
        }
        console.log('json6', json6);
        if (stdio_WebSocket != null) {
            showStep('request', json6);
            stdio_WebSocket.send(JSON.stringify(json6));
        } else {
            await sendSseMessage(json6, function (headers, json) {
                //mcp streamable-http 执行后返回的就是执行结果
                if (sse == false) {
                    mcp_calls[ii]();
                    showCallResult(json, type);
                }
            });
        }
    });
    itemDiv.appendChild(button);
    var propertie_index = 0;
    var properties = null;

    function createPropertie(type, propertie) {
        const span = document.createElement('span');
        propertie_index++;
        var required = null;
        if (type == "tools") {
            if (item.inputSchema.required) {
                required = item.inputSchema.required.includes(propertie);
            }
        } else if (type == "prompts") {
            required = propertie.required;
        }
        console.log(propertie, required);
        var required_span = '';
        if (required) {
            required_span = "<span style='color:red;'>*</span>";
        }
        var name = propertie.hasOwnProperty('name') ? propertie.name : propertie;
        span.innerHTML = "  " + propertie_index + "、 " + name + ":" + required_span + " ";
        itemDiv.appendChild(span);

        var itemInput = document.createElement('input');
        // html 控件类型
        var propertiesType = '';
        if (type == "resources") {
            itemInput.type = 'input';
            itemInput.value = propertie.uri;
            itemInput.disabled = true;
            propertiesType = 'text';
        } else if (properties[propertie] != null && properties[propertie].type == 'number') {
            itemInput.type = 'number';
            propertiesType = 'number';
        } else {
            itemInput.type = 'input';
            propertiesType = 'text';
        }

        itemInput.className = name;
        itemInput.setAttribute('ttype', propertiesType);
        if (type == "resources") {
            itemInput.setAttribute('placeholder', propertie.description);
        } else if (propertie.hasOwnProperty('description')) {
            itemInput.setAttribute('placeholder', propertie.description);
        } else if (properties[propertie] != null && properties[propertie].hasOwnProperty('description')) {
            itemInput.setAttribute('placeholder', properties[propertie].description);
        }
        itemDiv.appendChild(itemInput);
    }

    if (type == "tools") {
        properties = item.inputSchema.properties;
        Object.keys(properties).forEach(function (propertie) {
            createPropertie(type, propertie);
        });
    } else if (type == "prompts") {
        properties = item.arguments;
        if (properties) {
            properties.forEach(function (propertie) {
                createPropertie(type, propertie);
            });
        }
    } else if (type == "resources") {
        item.name = "uri";
        createPropertie(type, item);
    }

    containerTd.appendChild(itemDiv);
}

//显示执行结果
function showCallResult(json, type) {
    var func = mcp_calls[json['id']];
    console.log('mcp_calls', mcp_calls, json['id'], func);
    if (func != null) {
        func();
    }
    if (json['result']) {
        if (type == "tools") {
            if (json['result']['content'][0]['type'] == 'text') {
                alert('result is:' + json['result']['content'][0]['text']);
            }
        } else if (type == "prompts") {
            if (json['result']['messages'][0]['content']['type'] == 'text') {
                alert('result is:' + json['result']['messages'][0]['content']['text']);
            }
        } else if (type == "resources") {
            if (json['result']['contents'][0]['mimeType'] == 'text/plain') {
                alert('result is:' + json['result']['contents'][0]['text']);
            }
        }
    } else {
        alert('result is:' + json['params']['data']);
    }
}

async function sendSseMessage(jsonData, func) {
    showStep('request', jsonData);
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
            showStep('response', data);
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