var timer = setInterval(function () {
        window.scrollTo(0, document.body.scrollHeight);
        document.title = 'scroll running';
    }, 16),
    timer_status = !0;
document.onclick = function () {
    timer_status ? (timer_status = !1, clearInterval(timer),document.title = 'scroll stop') : (timer = setInterval(function () {
        window.scrollTo(0, document.body.scrollHeight);
        document.title = 'scroll running';
    }, 16), timer_status = !0)
};