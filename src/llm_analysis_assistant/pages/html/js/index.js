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

var div = document.createElement('div')
div.id = 'output';
div.style = 'white-space: pre-wrap;text-align: center;';
document.body.appendChild(div);
document.title = project_name + "(" + project_version + ")";
window.onload = startStream;