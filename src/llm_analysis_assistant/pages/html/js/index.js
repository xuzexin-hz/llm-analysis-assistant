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
    /*子链接显示效果*/
     .sub-links {
        position: absolute;
        background-color:#0c154582;
        padding: 11px 11px;
        border-radius: 12px;
        box-shadow: 0 0 12px rgb(240, 220, 130);
        z-index: 10;
        white-space: nowrap;
        opacity: 0;
        visibility: hidden;
        transition: opacity 3.6s ease, visibility 3.6s ease;
    }
    .sub-a {
        font-weight: bold;
        text-align: center;
        display: block;
        color: #fff;
        text-decoration: none;
        font-size: 30px;
        margin: 6px 0;
    }
    .sub-a:hover {
        color: #bf7dda;
    }
    `;
var base_url = location.pathname;
document.body.appendChild(style);
const links = [
    {
        text: 'mcp',
        href: base_url + 'mcp',
        cid: 'hour',
        pcl: 'hour-parent'
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
const sub_links = [
    {
        text: 'streamable-http',
        href: base_url + 'mcp?url=http://127.0.0.1:8001/mcp'
    },
    {
        text: 'stdio',
        href: base_url + 'mcp?url=stdio'
    },
    {
        text: 'sse',
        href: base_url + 'mcp?url=http://127.0.0.1:8002/sse'
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
    if (link.pcl) {
        a.classList.add(link.pcl);
    }
    container.appendChild(a);
});
const subs = document.createElement('div');
subs.className = 'sub-links';
subs.id = 'sub-links';
// 强调循序渐进和强调效率、重点明确 2种模式
const timeZoneOffset = new Date().getTimezoneOffset();
if (timeZoneOffset === -480) {
    sub_links.reverse();
}
sub_links.forEach(link => {
    const a = document.createElement('a');
    a.className = 'sub-a';
    a.href = link.href;
    a.target = '_blank';
    a.innerHTML = link.text;
    subs.appendChild(a);
});
container.appendChild(subs);
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

    const hourParent = document.querySelector('.hour-parent');
    const subLinks = document.getElementById('sub-links');
    var subLinksShow = false;

    function subLinks_Show() {
        paused = true;
        subLinksShow = true;
        const rect = hourParent.getBoundingClientRect();
        const containerRect = hourParent.closest('.a-container').getBoundingClientRect();
        subLinks.style.top = `${rect.top - containerRect.top}px`;
        subLinks.style.left = `${rect.right - containerRect.left}px`;
        subLinks.style.transform = `translateX(0px)`;
        subLinks.style.opacity = '1';
        subLinks.style.visibility = 'visible';
        subLinks.style.display = 'block';
    }

    function subLinks_Hide() {
        paused = false;
        subLinks.style.opacity = '0';
        subLinksShow = false;
        subLinks.addEventListener('transitionend', function handler() {
            if (subLinksShow == false) {
                subLinks.style.visibility = 'hidden';
                subLinks.removeEventListener('transitionend', handler);
                subLinks.style.display = 'none';
            }
        });
    }

    hourParent.addEventListener('mouseenter', () => {
        subLinks_Show();
    });
    subLinks.addEventListener('mouseenter', () => {
        subLinks_Show();
    });
    subLinks.addEventListener('mouseleave', () => {
        subLinks_Hide();
    });
    hourParent.addEventListener('mouseleave', () => {
        subLinks_Hide();
    });
}