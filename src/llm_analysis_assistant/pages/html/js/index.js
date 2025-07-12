async function startStream() {
    const response = await fetch('/?stream=true');
    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
        const {
            done,
            value
        } = await reader.read();
        if (done) break;
        document.getElementById('output').innerHTML += decoder.decode(value);
    }
}

document.title = project_name + "(" + project_version + ")";
window.onload = startStream;

const style = document.createElement("style");
style.innerText =
    `
        /*显示链接效果*/
        .a-container {
          display: flex;
          gap: 30px;
        }
        .a-type {
          margin: 0px;
          padding: 0px 12px;
          text-decoration: none;
          color: white;
          background-color: #0c154582;
          border-radius: 22px;
          font-size: 24px;
          font-weight: bold;
          transition: transform 0.3s ease, background-color 0.3s ease;
          position: relative;
        }
        .a-type:hover {
          background-color: #bf7dda;
          transform: scale(1.1);
        }
        .label {
          display: block;
          font-size: 14px;
          color: #ccc;
          margin-bottom: 5px;
        }
        .value {
          font-size: 32px;
          color: white;
        }
    `;
var base_url = location.pathname;
document.body.appendChild(style);
const links = [
    {
        text: 'mcp',
        href: base_url + 'mcp',
        cid: 'hour'
    },
    {
        text: 'logs',
        href: base_url + 'logs',
        cid: 'minute'
    },
    {
        text: 'test',
        href: base_url + 'stream',
        cid: 'second'
    },
];
const container = document.createElement('div');
container.className = 'a-container';
links.forEach(link => {
    const a = document.createElement('a');
    var label = document.createElement('span');
    label.className = 'label';
    label.innerHTML = link.text;
    a.appendChild(label);
    var value = document.createElement('span');
    value.className = 'value';
    value.id = link.cid;
    value.innerText = '--';
    a.appendChild(value);
    a.href = link.href;
    a.target = '_blank';
    a.classList.add('a-type');
    container.appendChild(a);
});
document.body.appendChild(container);
var div = document.createElement('div')
div.id = 'output';
div.style = 'white-space: pre-wrap;text-align: center;';
document.body.appendChild(div);
links_Animation();

function links_Animation() {
    const hourEl = document.getElementById('hour');
    const minuteEl = document.getElementById('minute');
    const secondEl = document.getElementById('second');
    const links = document.querySelectorAll('.a-type');
    let paused = false;
    let tick = 0;

    function pad(n) {
        return n < 10 ? '0' + n : n;
    }

    function updateTime() {
        if (!paused) {
            const now = new Date();
            hourEl.textContent = pad(now.getHours());
            minuteEl.textContent = pad(now.getMinutes());
            secondEl.textContent = pad(now.getSeconds());
        }
    }

    function animate() {
        if (!paused) {
            tick += 0.005;
            links.forEach((el, i) => {
                const y = Math.sin(tick + i) * 10;
                el.style.transform = `translateY(${y}px)`;
            });
        }
        requestAnimationFrame(animate);
    }

    setInterval(updateTime, 1000);
    updateTime();
    animate();

    links.forEach(el => {
        el.addEventListener('mouseenter', () => paused = true);
        el.addEventListener('mouseleave', () => paused = false);
    });
}