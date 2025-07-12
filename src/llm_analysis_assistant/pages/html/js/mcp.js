function load() {
    document.title = project_name + "(" + project_version + ")";
    var newDbg = document.createElement('div');
    newDbg.className = 'background';
    document.body.appendChild(newDbg);
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
    style.innerText =
        `
        /*按钮点击后的扫灯效果*/
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
        /*显示图片效果*/
        .fade-out-background {
            background-size: contain;
            background-repeat: no-repeat;
            background-position: center;
            width: 500px;
            height: 500px;
            animation: fadeOut 5s linear forwards;
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            overflow: hidden;
            z-index: 999;
        }
        @keyframes fadeOut {
            0% {
                opacity: 1;
            }
            100% {
                opacity: 0;
            }
        }
        /*显示链接效果*/
        .a-container {
          display: flex;
          gap: 30px;
        }
        .a-type {
            margin: 10px;
            padding: 10px;
            text-decoration: none;
            color: white;
            background-color: #0c154582;
            border-radius: 22px;
            transition: transform 0.3s ease, background-color 0.3s ease;
        }
        .a-type:hover {
            background-color: #bf7dda;
        }
    `;
    document.body.appendChild(style);
}
load();

// sse url or streamable-http url
var url = getParams('url', window.location.search);
// sse 返回的带session的地址
var sse_session_url = '';
// html上显示请求响应日志的自增序号
var num = 0;
// mcp 接口唯一标识，mcp初始化时候id为0即可
var index_id = 0;
// mcp调用集合
var mcp_calls = {};
// mcp streamable-http地址
var mcp_href = null;
// mcp streamable-http 附加头，目前是mcp-session-id
var mcp_headers_extra = {};
var ii = 0;

function dynamic_fields(obj, has_progressToken, only_url) {
    if (!only_url) {
        // 动态设置id
        Object.defineProperty(obj, 'id', {
            get: function () {
                return ii;
            },
            enumerable: true,
            configurable: true
        });
    }
    // 动态设置url
    Object.defineProperty(obj, 'url', {
        get: function () {
            return sse_session_url;
        },
        enumerable: true,
        configurable: true
    });
    if (has_progressToken) {
        Object.defineProperty(obj.params._meta, 'progressToken', {
            get: function () {
                return ii;
            },
            enumerable: true,
            configurable: true
        });
    }
}

//step1 初始化
var initialize_json = {
    "url": sse_session_url,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-06-18",
        "capabilities": {
            "sampling": {},
            "roots": {
                "listChanged": true
            }
        },
        "clientInfo": {
            "name": project_name,
            "version": project_version
        }
    },
    "jsonrpc": "2.0",
    "id": ii
};
dynamic_fields(initialize_json);

//step2 notifications/initialized
var notifications_initialized_json = {
    "url": sse_session_url,
    "jsonrpc": "2.0",
    "method": "notifications/initialized"
};
dynamic_fields(notifications_initialized_json, false, true);

//step 获取tools
var tools_list_json = {
    "url": sse_session_url,
    "method": "tools/list",
    "params": {
        "_meta": {
            "progressToken": ii
        }
    },
    "jsonrpc": "2.0",
    "id": ii
};
dynamic_fields(tools_list_json, true);

//step 获取prompts
var prompts_list_json = {
    "url": sse_session_url,
    "method": "prompts/list",
    "params": {
        "_meta": {
            "progressToken": ii
        }
    },
    "jsonrpc": "2.0",
    "id": ii
};
dynamic_fields(prompts_list_json, true);

//step 获取resources
var resources_list_json = {
    "url": sse_session_url,
    "method": "resources/list",
    "params": {
        "_meta": {
            "progressToken": ii
        }
    },
    "jsonrpc": "2.0",
    "id": ii
};
dynamic_fields(resources_list_json, true);

//step 获取resources/templates
var resources_templates_list_json = {
    "url": sse_session_url,
    "method": "resources/templates/list",
    "params": {
        "_meta": {
            "progressToken": ii
        }
    },
    "jsonrpc": "2.0",
    "id": ii
};
dynamic_fields(resources_templates_list_json, true);

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
    index_id++;
    return index_id;
}

var stdio_WebSocket = null;
var stdio_step = 0;
if (url == 'stdio') {
    var stdio_command = localStorage.getItem('stdio_command');
    var command = prompt(
        "Please enter the stdio service command(like:python -m mcp_server_time --local-timezone=Asia/Shanghai ++user=xxx)",
        localStorage.hasOwnProperty(
            'stdio_command') ? stdio_command :
        "python -m mcp_server_time --local-timezone=Asia/Shanghai ++user=xxx");
    if (command == null) {
        alert('User cancels operation');
        throw new Error("User cancels operation");
    }
    if (command == '') {
        alert('command is null');
        throw new Error("command is null");
    }
    localStorage.setItem('stdio_command', command);
    const container = document.querySelector('.container');
    const div = document.createElement('div');
    div.className = 'container-stdio';
    div.style = "border: 2px dotted;color: red;";
    div.innerText = "Stdio command is: " + command;
    if (container.firstChild) {
        container.insertBefore(div, container.firstChild);
    } else {
        container.appendChild(div);
    }

    stdio_WebSocket = new WebSocket('ws://localhost:' + ws_port + '/sse_ws?url=stdio&command=' + encodeURIComponent(
        command));
    window.stdio_WebSocket = stdio_WebSocket;
    stdio_WebSocket.onopen = async () => {
        console.log('stdio_WebSocket:Connected to WebSocket server');
        await mcpStdio();
    };
    stdio_WebSocket.onmessage = async (event) => {
        var json = isValidJSON(event.data);
        showStep('response', json);
        if (json) {
            if (!json['logger']) {
                stdio_step = stdio_step + 1;
                await mcpStdio();
            }
            if (json['result']) {
                //判断包含哪些资源
                if (json['result']['capabilities']) {
                    if (json['result']['capabilities']['tools']) {
                        await mcpStdio('tools');
                    }
                    if (json['result']['capabilities']['prompts']) {
                        await mcpStdio('prompts');
                    }
                    if (json['result']['capabilities']['resources']) {
                        await mcpStdio('resources');
                        await mcpStdio('resourceTemplates');
                    }
                } else {
                    await showResultAndCall(json);
                }
            } else {
                if (json == false) {
                    alert(event.data);
                }
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
    var mcp = null;
    if (URL.canParse(url)) {
        mcp = new URL(url);
    }
    if (url == null || mcp == null || !(mcp.pathname.endsWith('/sse') || mcp.pathname.endsWith('/mcp'))) {
        var base_url = location.pathname;
        const container = document.createElement('div');
        container.className = 'a-container';
        const links = [
            {
                text: 'streamable-http',
                href: base_url + '?url=http://127.0.0.1:8001/mcp'
            },
            {
                text: 'stdio',
                href: base_url + '?url=stdio'
            },
            {
                text: 'sse',
                href: base_url + '?url=http://127.0.0.1:8002/sse'
            },
        ];
        // 强调循序渐进和强调效率、重点明确 2种模式
        const timeZoneOffset = new Date().getTimezoneOffset();
        if (timeZoneOffset === -480) {
            links.reverse();
        }
        links.forEach(link => {
            const a = document.createElement('a');
            a.innerHTML = link.text;
            a.href = link.href;
            a.target = '_blank';
            a.classList.add('a-type');
            container.appendChild(a);
        });
        document.body.appendChild(container);
        let paused = false;
        let tick = 0;
        const a_links = document.querySelectorAll('.a-type');

        function animate() {
            if (!paused) {
                tick += 0.005;
                a_links.forEach((el, i) => {
                    const y = Math.sin(tick + i) * 10;
                    el.style.transform = `translateY(${y}px)`;
                });
            }
            requestAnimationFrame(animate);
        }

        animate();
        a_links.forEach(el => {
            el.addEventListener('mouseenter', () => paused = true);
            el.addEventListener('mouseleave', () => paused = false);
        });

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
            await mcpSSE(json, event);
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

//显示资源及调用结果
async function showResultAndCall(json) {
    //获取资源后要显示一便于用户调用
    if (json['result']['tools']) {
        await showGetResult('tools', json, true);
    } else if (json['result']['prompts']) {
        await showGetResult('prompts', json, true);
    } else if (json['result']['resources']) {
        await showGetResult('resources', json, true);
    } else if (json['result']['resourceTemplates']) {
        await showGetResult('resourceTemplates', json, true);
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
}

//mcp streamable-http 调用过程
async function mcpStreamableHttp() {
    // 这样设置，后台处理时候可以兼容llm设置mcp，该服务可以监测的
    mcp_href = location.href;
    console.log('initialize_json', initialize_json);
    var json = {};
    var res = await sendSseMessageAsync(initialize_json, function (headers, data) {
        json = data;
    });
    console.log('json', json);
    var headers = res.headers;
    console.log('notifications_initialized_json', notifications_initialized_json);
    if (headers.get('mcp-session-id') != null) {
        mcp_headers_extra = {
            'mcp-session-id': headers.get('mcp-session-id')
        }
    }
    await sendSseMessageAsync(notifications_initialized_json);
    if (json['result']['capabilities']) {
        if (json['result']['capabilities']['tools']) {
            ii = getIndex();
            console.log('tools_list_json', tools_list_json);
            await sendSseMessageAsync(tools_list_json, async function (headers, data) {
                await showGetResult("tools", data, false);
            });
        }
        if (json['result']['capabilities']['prompts']) {
            ii = getIndex();
            console.log('prompts_list_json', prompts_list_json);
            await sendSseMessageAsync(prompts_list_json, async function (headers, data) {
                await showGetResult("prompts", data, false);
            });
        }
        if (json['result']['capabilities']['resources']) {
            ii = getIndex();
            console.log('resources_list_json', resources_list_json);
            await sendSseMessageAsync(resources_list_json, async function (headers, data) {
                showGetResult("resources", data, false);
            });

            ii = getIndex();
            console.log('resources_templates_list_json', resources_templates_list_json);
            await sendSseMessageAsync(resources_templates_list_json, async function (headers, data) {
                showGetResult("resourceTemplates", data, false);
            });
        }
    }
}

//mcp stdio 调用过程
async function mcpStdio(type) {
    console.log('stdio_step', stdio_step);
    if (type == 'tools') {
        ii = getIndex();
        console.log('tools_list_json', tools_list_json);
        await toStdioMsg(tools_list_json, 200);
    } else if (type == 'prompts') {
        ii = getIndex();
        console.log('prompts_list_json', prompts_list_json);
        await toStdioMsg(prompts_list_json, 200);
    } else if (type == 'resources') {
        ii = getIndex();
        console.log('resources_list_json', resources_list_json);
        await toStdioMsg(resources_list_json, 200);
    } else if (type == 'resourceTemplates') {
        ii = getIndex();
        console.log('resources_templates_list_json', resources_templates_list_json);
        await toStdioMsg(resources_templates_list_json, 200);
    } else if (stdio_step == 0) {
        // id 默认为0
        console.log('initialize_json', initialize_json);
        await toStdioMsg(initialize_json);
    } else if (stdio_step == 1) {
        console.log('notifications_initialized_json', notifications_initialized_json);
        await toStdioMsg(notifications_initialized_json);
    }
}

//stdio使用
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

//mcp sse 调用过程
async function mcpSSE(json_in, event) {
    if (json_in) {
        console.log('sse_WebSocket', json_in);
        showStep('response', json_in);
        if (json_in['event'] == 'endpoint') {
            sse_session_url = (new URL(url)).origin + json_in['data'];
            console.log('initialize_json', initialize_json);
            await sendSseMessageAsync(initialize_json);
        } else {
            var json = json_in['data'];
            if (json['result']) {
                if (json['result']['protocolVersion']) {
                    console.log('notifications_initialized_json', notifications_initialized_json);
                    await sendSseMessageAsync(notifications_initialized_json, async function () {
                        if (json['result']['capabilities']['tools']) {
                            await nextStep('tools');
                        }
                        if (json['result']['capabilities']['prompts']) {
                            await nextStep('prompts');
                        }
                        if (json['result']['capabilities']['resources']) {
                            await nextStep('resources');
                            await nextStep('resourceTemplates');
                        }
                    });
                } else {
                    await showResultAndCall(json);
                }
            } else {
                if (json == false) {
                    alert(event.data);
                }
            }
        }
    } else {
        if (json_in == false) {
            alert(event.data);
        }
    }
}

//sse 使用
async function nextStep(type) {
    if (type == 'tools') {
        ii = getIndex();
        console.log('tools_list_json', tools_list_json);
        await sendSseMessageAsync(tools_list_json);
    } else if (type == 'prompts') {
        ii = getIndex();
        console.log('prompts_list_json', prompts_list_json);
        await sendSseMessageAsync(prompts_list_json);
    } else if (type == 'resources') {
        ii = getIndex();
        console.log('resources_list_json', resources_list_json);
        await sendSseMessageAsync(resources_list_json);
    } else if (type == 'resourceTemplates') {
        ii = getIndex();
        console.log('resources_templates_list_json', resources_templates_list_json);
        await sendSseMessageAsync(resources_templates_list_json);
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
        if (json.hasOwnProperty('logger') && json['logger'] == 'info') {
            document.querySelector('.mcp').innerHTML += '<p style = \'color: red;\' >' + json['msg'] + '</p>';
            return;
        }
        if (json['data'] != undefined && typeof json['data'] === 'string') {
            if (isValidJSON(json['data'])) {
                var jj = JSON.parse(json['data']);
                json['data'] = jj;
            }
        }
        console.log('showStep2', json);
        if (json.hasOwnProperty('url') && json.url == '') {
            delete json.url;
        }
        formattedJson = JSON.stringify(json, null, 2);
    } else {
        formattedJson = data;
    }
    html = num + "、   ---" + t + ":" + '<pre class="jsonContainer" style="' + style + '">' + formattedJson + '</pre>' +
        '<br/>';
    document.querySelector('.mcp').innerHTML += html;
}

//显示获取结果
async function showGetResult(type, data, sse) {
    var jsonData = data;
    console.log('showGetResult+' + type + ":", jsonData);
    if (type == 'tools') {
        if (jsonData.result.tools.length > 0) {
            mcp2html(type);
        }
        for (const tool of jsonData.result.tools) {
            await showItem2Html(type, tool, sse);
        }
    } else if (type == 'prompts') {
        if (jsonData.result.prompts.length > 0) {
            mcp2html(type);
        }
        for (const tool of jsonData.result.prompts) {
            await showItem2Html(type, tool, sse);
        }
    } else if (type == 'resources') {
        if (jsonData.result.resources.length > 0) {
            mcp2html(type);
        }
        for (const resource of jsonData.result.resources) {
            await showItem2Html(type, resource, sse);
        }
    } else if (type == 'resourceTemplates') {
        if (jsonData.result.resourceTemplates.length > 0) {
            mcp2html(type);
        }
        for (const resource of jsonData.result.resourceTemplates) {
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
    td1.innerHTML = type;
    td2.className = type;
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
    button.style = "width:38px;height:26px;";
    var ref_count = 0;
    // 调用工具按钮点击事件
    button.addEventListener("click", async function () {
        changeSize(button, 2);
        button.className = "button";
        ref_count++;
        button.textContent = "0";
        var container = button.parentElement;
        var inputs = container.querySelectorAll("input");
        var inputData = {};
        inputs.forEach(function (input) {
            console.log(input.name, input.value);
            var value = input.value;
            if (input.getAttribute('ttype') == 'number') {
                value = Number(input.value);
            }
            if (input.getAttribute('required') == 'true') {
                if (value == '' || value == null) {
                    //这里只提示必填字段，但不阻止继续调用。这样也可看到参数异常时候的调用结果
                    alert(input.name + ' is required');
                }
            }
            inputData[input.name] = value;
        });
        var jsonData = JSON.stringify(inputData);
        console.log('jsonData', jsonData);
        var call_json = null;
        var ii = getIndex();
        if (type == "tools") {
            call_json = {
                "jsonrpc": "2.0",
                "id": ii,
                "url": sse_session_url,
                "method": "tools/call",
                "params": {
                    "_meta": {
                        "progressToken": ii
                    },
                    "name": item.name,
                    "arguments": inputData
                }
            }
        } else if (type == "prompts") {
            call_json = {
                "jsonrpc": "2.0",
                "id": ii,
                "url": sse_session_url,
                "method": "prompts/get",
                "params": {
                    "_meta": {
                        "progressToken": ii
                    },
                    "name": item.name,
                    "arguments": inputData
                }
            }
        } else if (type == "resources") {
            call_json = {
                "jsonrpc": "2.0",
                "id": ii,
                "url": sse_session_url,
                "method": "resources/read",
                "params": inputData
            }
        } else if (type == "resourceTemplates") {
            var uri = item.uriTemplate;
            Object.keys(inputData).forEach(key => {
                uri = uri.replace('{' + key + '}', inputData[key]);
            });
            call_json = {
                "jsonrpc": "2.0",
                "id": ii,
                "url": sse_session_url,
                "method": "resources/read",
                "params": {
                    "_meta": {
                        "progressToken": ii
                    },
                    "uri": uri
                }
            }
        }
        var item_timer_time = 0;
        var item_timer = setInterval(function () {
            item_timer_time++;
            button.textContent = item_timer_time;
        }, 1000);
        mcp_calls[ii] = function () {
            button.textContent = "test";
            changeSize(button, -2);
            ref_count--;
            if (ref_count <= 0) {
                button.className = "";
            }
            clearInterval(item_timer);
        }
        console.log('call_json', call_json);
        if (stdio_WebSocket != null) {
            showStep('request', call_json);
            stdio_WebSocket.send(JSON.stringify(call_json));
        } else {
            await sendSseMessage(call_json, function (headers, json) {
                //mcp streamable-http 执行后返回的就是执行结果
                if (sse == false) {
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
        } else if (type == "resourceTemplates") {
            required = true;
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
        itemInput.setAttribute('required', required);
        itemInput.style = "height:27px;";
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
        itemInput.name = name;
        itemInput.setAttribute('ttype', propertiesType);
        if (type == "resources") {
            itemInput.setAttribute('placeholder', propertie.description);
        } else if (propertie.hasOwnProperty('description')) {
            itemInput.setAttribute('placeholder', propertie.description);
        } else if (properties[propertie] != null && properties[propertie].hasOwnProperty('description')) {
            itemInput.setAttribute('placeholder', properties[propertie].description);
        }
        if (itemInput.getAttribute('placeholder') != null) {
            itemInput.setAttribute('title', itemInput.getAttribute('placeholder'));
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
    } else if (type == "resourceTemplates") {
        const matches = item.uriTemplate.match(/{(.*?)}/g);
        properties = matches ? matches.map(match => match.slice(1, -1)) : [];
        if (properties.length > 0) {
            properties.forEach(function (propertie) {
                createPropertie(type, propertie);
            });
        }
    }

    containerTd.appendChild(itemDiv);
}

//控制按钮长宽变化
function changeSize(obj, add_number) {
    let currentWidth = parseInt(window.getComputedStyle(obj).width);
    let currentHeight = parseInt(window.getComputedStyle(obj).height);
    obj.style.width = (currentWidth + add_number) + 'px';
    obj.style.height = (currentHeight + add_number) + 'px';
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
                if (json['result']['content'].length > 1) {
                    var list = [];
                    for (var i = 0; i < json['result']['content'].length; i++) {
                        list.push(json['result']['content'][i]['text']);
                    }
                    alert('result is:' + JSON.stringify(list));
                } else {
                    alert('result is:' + json['result']['content'][0]['text']);
                }
            } else if (json['result']['content'][0]['type'] == 'image') {
                var data = json['result']['content'][0]['data'];
                var mimeType = json['result']['content'][0]['mimeType'];
                var bg = document.querySelector('.background');
                var img = 'data:' + mimeType + ';base64,' + data;
                bg.style.backgroundImage = "url('" + img + "')";
                bg.classList.add('fade-out-background');

                function saveImage() {
                    const a = document.createElement('a');
                    a.href = img;
                    a.download = project_name + '.' + mimeType.split('/')[1];
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                }

                bg.addEventListener('click', saveImage);
                setTimeout(function () {
                    bg.classList.remove('fade-out-background');
                    bg.style.backgroundImage = '';
                    bg.removeEventListener('click', saveImage);
                }, 5000);
            }
        } else if (type == "prompts") {
            if (json['result']['messages'][0]['content']['type'] == 'text') {
                if (json['result']['messages'].length > 1) {
                    var list = [];
                    for (var i = 0; i < json['result']['messages'].length; i++) {
                        list.push(json['result']['messages'][i]['content']['text']);
                    }
                    alert('result is:' + JSON.stringify(list));
                } else {
                    alert('result is:' + json['result']['messages'][0]['content']['text']);
                }
            }
        } else if (type == "resources" || type == "resourceTemplates") {
            if (json['result']['contents'][0]['mimeType'] == 'text/plain') {
                if (json['result']['contents'].length > 1) {
                    var list = [];
                    for (var i = 0; i < json['result']['contents'].length; i++) {
                        list.push(json['result']['contents'][i]['text']);
                    }
                    alert('result is:' + JSON.stringify(list));
                } else {
                    alert('result is:' + json['result']['contents'][0]['text']);
                }
            }
        }
    } else {
        alert('result is:' + json['params']['data']);
    }
}

//mcp 显示资源时保证顺序便于理解
async function sendSseMessageAsync(jsonData, func) {
    return await myfetch(jsonData, func)
}

// 调用时候不需要等待，这样可以并发
function sendSseMessage(jsonData, func) {
    return myfetch(jsonData, func)
}

function myfetch(jsonData, func) {
    showStep('request', jsonData);
    var url = '/sse_msg';
    if (mcp_href != null) {
        url = mcp_href;
    }
    const headers = {
        'Content-Type': 'application/json'
    };
    const mergedHeaders = Object.assign({}, headers, mcp_headers_extra);
    return fetch(url, {
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
            alert(error);
            console.error('Error:', error);
        });
}