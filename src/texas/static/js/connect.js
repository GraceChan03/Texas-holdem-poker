Texas = {

    socket: null,

    GameRound: {
        roundId: null,
        dealerCards: null,

        setCard: function (card, $card) {
            width = 75;
            height = 125;
            x = 0;
            y = 0;
            var acard = card.split("");
            var rank = acard[0];
            var suit = acard[1];

            if (rank !== undefined && suit !== undefined) {
                switch (suit) {
                    case "s":
                        // Spades
                        x -= width;
                        y -= height;
                        break;
                    case "c":
                        // Clubs
                        y -= height;
                        break;
                    case "d":
                        // Diamonds
                        x -= width;
                        break;
                    case "h":
                        // Hearts
                        break;
                    default:
                        throw "Invalid suit";
                }

                switch (rank) {
                    case "A":
                        rank = 1;
                        break;
                    case "T":
                        rank = 10;
                        break;
                    case "J":
                        rank = 11;
                        break;
                    case "Q":
                        rank = 12;
                        break;
                    case "K":
                        rank = 13;
                        break;
                    default:
                        rank = parseInt(rank);
                        break;
                }

                if (rank < 1 || rank > 13) {
                    throw "Invalid rank";
                }

                x -= (rank - 1) * 2 * width + width;
            }

            $card.css('background-position', x + "px " + y + "px");
        },

        setPlayerCards: function (player_cards) {
            for (card in player_cards) {
                $card = $('#card' + card);
                Texas.GameRound.setCard(player_cards[card], $card);
            }
        },

        show3Cards: function (dealer_cards) {
            for (i = 0; i < 3; i++) {
                $card = $('#dealer_card' + i);
                Texas.GameRound.setCard(dealer_cards[i], $card);
            }
        },

        newGame: function (data) {
            Texas.GameRound.roundId = data.round_id;

            // get cards info
            var current_player = $("#current-player").val();
            var my_player_cards = data.player_cards[current_player];
            // set cards
            Texas.GameRound.setPlayerCards(my_player_cards);

            var dealer_cards = data.dealer_cards.split(",");
            Texas.GameRound.dealerCards = dealer_cards;
            // show three dealer cards
            Texas.GameRound.show3Cards(dealer_cards);
        },

        onRoundUpdate: function (data) {
            // reset timer if timers are set on game_ongoing.html

            switch (data.event) {
                case 'new-game':
                    Texas.GameRound.newGame(data);
                    break;
            }
        }
    },

    Player: {},

    Game: {
        gameNo: null,

        initGame: function (data) {
            Texas.Game.gameNo = data.game_no;
        },

        onGameUpdate: function (data) {
            if (Texas.Game.gameNo === null) {
                Texas.Game.initGame(data)
            }

            var current_player = $("#current-player").val();
            switch (data.event) {
                case 'player-add':
                    var list = $("#contact-list");
                    if (current_player !== data.userid.toString()) {
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
                    break;

                case 'player-remove':
                    break;
            }
        }
    },

    init: function () {
        var ws_scheme = window.location.protocol == "https:" ? "wss" : "ws";
        var userid = $('#current-player').val();
        Texas.socket = new WebSocket(ws_scheme + '://' + window.location.host + "/bet/" + userid + window.location.pathname);

        Texas.socket.onmessage = function (message) {
            var data = JSON.parse(message.data);

            switch (data.message_type) {
                case 'game-update':
                    Texas.Game.onGameUpdate(data);
                    break;
                case 'round-update':
                    Texas.GameRound.onRoundUpdate(data);
                    break;
            }
        }
    }
}


$(document).ready(function () {
    Texas.init();
})