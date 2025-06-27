var timer = setInterval(function () {
        window.scrollTo(0, document.body.scrollHeight);
        document.title = 'scroll running';
    }, 16),
    timer_status = !0;
document.ondblclick = function () {
    timer_status ? (timer_status = !1, clearInterval(timer), document.title = 'scroll stop') : (timer = setInterval(
        function () {
            window.scrollTo(0, document.body.scrollHeight);
            document.title = 'scroll running';
        }, 16), timer_status = !0)
};

document.addEventListener('DOMContentLoaded', function () {
    var newP = document.createElement('p');
    newP.className = 'logs';
    document.body.appendChild(newP);
});

function isValidJSON(str) {
    try {
        return JSON.parse(str); // 如果解析成功，返回解析后的对象
    } catch (e) {
        return false; // 如果出现错误，返回 false
    }
}

const ws = new WebSocket('ws://localhost:' + ws_port + '/logs_ws');
ws.onopen = () => {
    console.log('Connected to WebSocket server');
};
ws.onmessage = (event) => {
    var json = isValidJSON(event.data);
    console.log(json);
    if (json) {
        var data = isValidJSON(json['data']['data']);
        if (data) {
            var style = '';
            if (json['type'] == 'req' || json['type'] == 'sseq') {
                style = 'color: blue;';
            } else if (json['type'] == 'res' || json['type'] == 'sses') {
                style = 'color: green;';
            } else if (json['type'] == 'rec') {
                style = 'color: red;';
            }
            var formattedJson = JSON.stringify(data, null, 2);
            document.querySelector('.logs').innerHTML += json['line_num'] + ': ' + '<pre class="jsonContainer" style="' + style + '">' + formattedJson + '</pre>' + '<br/>';
        } else {
            document.querySelector('.logs').innerHTML += json['line_num'] + ': ' + json['data']['data'] + '<br/>';
        }
    } else {
        document.querySelector('.logs').innerHTML += event.data;
    }
};
ws.onclose = () => {
    console.log('Disconnected from WebSocket server');
};