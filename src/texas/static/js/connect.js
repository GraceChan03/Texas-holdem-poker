$(function () {
    var ws_scheme = window.location.protocol == "https:" ? "wss" : "ws";
    var username = $('#username').val();
    var betsock = new WebSocket(ws_scheme + '://' + window.location.host + "/bet/" + username + window.location.pathname);

    betsock.onmessage = function (message) {
        var data = JSON.parse(message.data);
        var list = $("#contact-list");
        var current_player = $("#username").val();

        if (current_player !== data.username) {
            var ele = $('<li class="list-group-item"></li>');
            var div1 = $('<div class="col-xs-12 col-sm-3"></div>');
            div1.append($("<img>").attr({
                src: "/" + data.photo_src,
                alt: "Scott Stevens",
                class: "img-responsive img-circle"
            }));
            div1.append($("<span></span>").attr({
                class: "login-link"
            }).text(data.username));
            div1.append($("<br>"));
            ele.append(div1);
            var div2 = $('<div class="col-xs-12 col-sm-9"></div>');
            ele.append(div2);
            var div3 = $('<div class="clearfix"></div>');
            ele.append(div3);
            list.append(ele);
        }

    }
});