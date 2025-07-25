var timer = setInterval(function () {
        window.scrollTo(0, document.body.scrollHeight);
        document.title = project_name + ' scroll running';
    }, 16),
    timer_status = !0;
document.ondblclick = function () {
    timer_status ? (timer_status = !1, clearInterval(timer), document.title = project_name + ' scroll stop') : (
        timer = setInterval(
            function () {
                window.scrollTo(0, document.body.scrollHeight);
                document.title = project_name + ' scroll running';
            }, 16), timer_status = !0)
};

document.addEventListener('DOMContentLoaded', function () {
    var newP = document.createElement('p');
    newP.className = 'logs';
    document.body.appendChild(newP);
    const container = document.querySelector('body');
    const button = document.createElement('button');
    button.className = 'clear';
    button.textContent = "clear";
    button.style = "height:25px;";
    button.style.display = 'none';
    button.addEventListener("click", function () {
        document.querySelector('.logs').innerHTML = '';
        button.style.display = 'none';
    });
    if (container.firstChild) {
        container.insertBefore(button, container.firstChild);
    } else {
        container.appendChild(button);
    }
});

function isValidJSON(str) {
    try {
        return JSON.parse(str); // 如果解析成功，返回解析后的对象
    } catch (e) {
        return false; // 如果出现错误，返回 false
    }
}

let latest_time = 0;
if (sessionStorage.getItem('latest_time') != null) {
    latest_time = sessionStorage.getItem('latest_time');
}
let ws;
let retry_count = 0;

function connectWebSocket() {
    ws = new WebSocket('ws://localhost:' + ws_port + '/logs_ws?tt=' + latest_time);
    ws.onopen = () => {
        console.log('Connected to WebSocket server');
    };
    ws.onmessage = (event) => {
        var json = isValidJSON(event.data);
        console.log(json);
        var clearBtn = document.querySelector('.clear');
        clearBtn.style.display = 'block';
        if (json) {
            if (json.hasOwnProperty('file') && json.hasOwnProperty('ctime')) {
                latest_time = json['ctime'];
                sessionStorage.setItem('latest_time', latest_time);
                document.querySelector('.logs').innerHTML += json['file'];
                return
            }
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
                document.querySelector('.logs').innerHTML += json['line_num'] + ': ' +
                    '<pre class="jsonContainer" style="' + style + '">' + formattedJson + '</pre>' + '<br/>';
            } else {
                document.querySelector('.logs').innerHTML += json['line_num'] + ': ' + json['data']['data'] +
                    '<br/>';
            }
        } else {
            document.querySelector('.logs').innerHTML += event.data;
        }
    };
    ws.onclose = () => {
        console.log('Disconnected from WebSocket server');
        ws.close();
        console.log((1 + retry_count) + "s后重连");
        setTimeout(function () {
            connectWebSocket();
        }, (1 + retry_count) * 1000);
        retry_count++;
    };
}

connectWebSocket();