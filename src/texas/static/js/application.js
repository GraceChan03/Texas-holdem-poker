Texas = {

    socket: null,

    GameRound: {
        roundId: null,
        dealerCards: null,
        dealerCardTurn: null,

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

        turnoverCard: function () {
            var turn = Texas.GameRound.dealerCardTurn;
            $card = $('#dealer_card' + turn);
            Texas.GameRound.setCard(Texas.GameRound.dealerCards[i], $card);
            Texas.GameRound.dealerCardTurn += 1;
        },

        setPlayerFunds: function (player_funds) {
            var funds = JSON.parse(player_funds);
            for (player in funds) {
                $('#txt_fund_' + player).css('visibility', 'visible')
                    .text("Current Fund: " + funds[player]);
                if (player.toString() === $('#current-player-id').val()) {
                    $('#my_fund').css('visibility', 'visible').text("My chips: " + funds[player]);
                }
            }
        },

        gameOver: function (data) {
            Texas.Player.disableLastTurn();
            $('#page_title').text(data.winner + " wins! Congratulations!");
        },

        newRound: function (data) {
            Texas.GameRound.roundId = data.round_id;

            // get cards info
            var current_player = $("#current-player-id").val();
            var my_player_cards = data.player_cards[current_player];
            // set cards
            Texas.GameRound.setPlayerCards(my_player_cards);
            Texas.GameRound.setPlayerFunds(data.player_funds);

            var dealer_cards = data.dealer_cards.split(",");
            Texas.GameRound.dealerCards = dealer_cards;
            Texas.GameRound.dealerCardTurn = 3;
            // show three dealer cards
            Texas.GameRound.show3Cards(dealer_cards);
        },

        onRoundUpdate: function (data) {
            // reset timer if timers are set on game_ongoing.html

            switch (data.event) {
                case 'new-game':
                    Texas.GameRound.newRound(data);
                    break;
                case 'player-action':
                    Texas.Player.onPlayerAction(data);
                    break;
                case 'add-dealer-card':
                    Texas.GameRound.turnoverCard();
                    break;
                case 'game-over':
                    Texas.GameRound.gameOver(data);
                    break;

            }
        }
    },

    Player: {
        betMode: false,
        currPlayer: null,

        resetTimers: function () {

        },

        setBetVisible: function (data) {
            var min = data.min_bet; // the minimum fund that a player should pay to bet
            var max = data.max_bet; // the maximum fund that a player is able to bet
            // all in
            if (min >= max) {
                $('#btn_fold').css('visibility', 'visible');
                $('#btn_allin').css('display', 'inline');
            } else {
                $('#btn_check').css('visibility', 'visible');
                $('#btn_fold').css('visibility', 'visible');
                $('#btn_bet').css('visibility', 'visible');
                var slider = $('#myRange');
                slider.attr({
                    min: data.min_bet,
                    max: data.max_bet,
                    value: data.min_bet
                });
                var output = $('#demo');
                output.text(slider.val());
                slider.on('input', function () {
                    output.text($(this).val())
                });
                $('#chips').css('visibility', 'visible');
            }
        },

        setBetInVisible: function () {
            $('#btn_check').css('visibility', 'hidden');
            $('#btn_fold').css('visibility', 'hidden');
            $('#btn_bet').css('visibility', 'hidden');
            $('#chips').css('visibility', 'hidden');
        },

        enableBetMode: function (data) {
            Texas.Player.betMode = true;
            Texas.Player.setBetVisible(data);
        },

        disableBetMode: function () {
            Texas.Player.betMode = false;
            Texas.Player.setBetInVisible();
        },

        disableLastTurn: function () {
            if (Texas.Player.currPlayer !== null) {
                $('#txt_turn_' + Texas.Player.currPlayer).css('visibility', 'hidden');
            }
        },

        onPlayerAction: function (data) {
            isCurrentPlayer = data.player.userid.toString() === $('#current-player-id').val();


            if (isCurrentPlayer) {
                Texas.Player.enableBetMode(data);
            }
            // renew the pot
            $('#pot').text("Pot: " + data.pot);
            // disable last turn
            Texas.Player.disableLastTurn();
            // enable this turn
            Texas.Player.currPlayer = data.player.userid;
            var id = data.player.userid;
            var username = data.player.username;
            $('#txt_turn_' + id).text(username + "'s turn").css('visibility', 'visible');
            // set timers
        }

    },

    Game: {
        gameNo: null,

        initGame: function (data) {
            Texas.Game.gameNo = data.game_no;
            // initialize the room
            $('#players').empty();
            // set seats == player_num (decides by creator)
            for (i in data.player_num) {

            }
        },

        onGameUpdate: function (data) {
            if (Texas.Game.gameNo === null) {
                Texas.Game.initGame(data)
            }

            var current_player_id = $("#current-player-id").val();
            switch (data.event) {
                case 'player-add':
                    var list = $("#contact-list");
                    if (current_player_id !== data.userid.toString()) {
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
                        div2.append($("<span></span>").attr({
                            id: "txt_fund_" + data.userid,
                            class: "txt-fund"
                        }));
                        div2.append($("<br><br>"));
                        div2.append($("<span></span>").attr({
                            id: "txt_turn_" + data.userid,
                            class: "txt-turn"
                        }));
                        div2.append($("<br>"));
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
        var userid = $('#current-player-id').val();
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
        };

        $('#btn_check').click(function () {
            Texas.socket.send(JSON.stringify({
                'message_type': 'bet',
                'bet': 0,
                'round_id': Texas.GameRound.roundId
            }));
            Texas.Player.disableBetMode();
        });

        $('#btn_fold').click(function () {
            Texas.socket.send(JSON.stringify({
                'message_type': 'bet',
                'bet': -1,
                'round_id': Texas.GameRound.roundId
            }));
            Texas.Player.disableBetMode();
        });

        $('#btn_bet').click(function () {
            Texas.socket.send(JSON.stringify({
                'message_type': 'bet',
                'bet': $('#myRange').val(),
                'round_id': Texas.GameRound.roundId
            }));
            Texas.Player.disableBetMode();
        })

        $('#btn_allin').click(function () {
            Texas.socket.send(JSON.stringify({
                'message_type': 'bet',
                'bet': $('#myRange').val(),
                'round_id': Texas.GameRound.roundId
            }));
            Texas.Player.disableBetMode();
        });
    }
}


$(document).ready(function () {
    Texas.init();
})