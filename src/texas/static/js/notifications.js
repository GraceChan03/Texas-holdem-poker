$(document).ready(function () {
    setInterval(getRequests, 5000);
    $('.notification').click(disableNotification);

    // CSRF set-up copied from Django docs
    function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
    }
    var csrftoken = getCookie('csrftoken');
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    });
});

function getRequests() {
    $.ajax({
        url: "/check_friend_requests",
        type: "get",
        success: function(data){
            if (data != 0 && $('.notification').attr('notify') == 'false') {
                var span = $('<span></span>');
                span.addClass("badge").addClass("badge-pill").addClass("badge-danger");
                span.addClass("friend-request");
                span.text(data);
                $('.notification').append(span);
                $('.notification').attr('notify', 'true');
            }
        }
    })
}

function disableNotification() {
    $.ajax({
        url: "/disable_notification",
        type: "post",
        data: {"timestamp" : $.now()},
        success: function () {
            $('.friend-request').remove();
            $('.notification').attr('notify', 'false');
        }
    })
}