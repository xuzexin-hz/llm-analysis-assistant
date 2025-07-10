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

const style = document.createElement("style");
style.innerText =
    `
        /*显示链接效果*/
        .a-type {
            margin: 10px;
            padding: 10px;
            text-decoration: none;
            color: white;
            background-color: #0c154582;
            border-radius: 22px;
        }
        .a-type:hover {
            background-color: #bf7dda;
        }
    `;
var base_url = location.pathname;
document.body.appendChild(style);
const links = [
    {
        text: 'logs',
        href: base_url + 'logs'
    },
    {
        text: 'mcp',
        href: base_url + 'mcp'
    },
    {
        text: 'test',
        href: base_url + 'stream'
    },
];
links.forEach(link => {
    const a = document.createElement('a');
    a.innerHTML = link.text;
    a.href = link.href;
    a.target = '_blank';
    a.classList.add('a-type');
    document.body.appendChild(a);
});
var div = document.createElement('div')
div.id = 'output';
div.style = 'white-space: pre-wrap;text-align: center;';
document.body.appendChild(div);
document.title = project_name + "(" + project_version + ")";
window.onload = startStream;