$(document).ready(function () {
    $('.chips').material_chip();
    $('.chips-autocomplete').material_chip({
        autocompleteOptions: {
            data: {
                'Apple': null,
                'Microsoft': null,
                'Google': null
            },
            limit: Infinity,
            minLength: 1
        }
    });

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
        beforeSend: function (xhr, settings) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    });
});

function sendFriendInvitation() {
    var player_no = parseInt($('#player_no').val());
    var data = $('.chips').material_chip('data');
    if (player_no < data.length) {
        $('.invite-warning').text("You can only invite" + (player_no - 1) + "players");
    }
    if (data.length > 0) {
        var friends = "";
        for (i in data) {
            friends += data[i].tag + "|";
        }
        $('.chip').remove();
        $.ajax({
            url: "/station_invite",
            type: "post",
            data: {"friends": friends, "game_no": $('#game_no').val()},
            success: function (data) {
                if (data != 'success') {
                    $('.invite-warning').text("Invitation fail. Please check your friends' name");
                }
            }
        })
    }
}