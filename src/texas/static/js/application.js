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
                $card.css('visibility', 'visible');
            }
        },

        turnoverCard: function (data) {
            var dealer_cards = data.dealer_cards.split(",");
            if (dealer_cards.length === 3) {
                Texas.GameRound.dealerCardTurn = 3;
                Texas.GameRound.show3Cards(dealer_cards);
            } else {
                var turn = Texas.GameRound.dealerCardTurn;
                $card = $('#dealer_card' + turn);
                Texas.GameRound.setCard(dealer_cards[0], $card);
                $card.css('visibility', 'visible');
                Texas.GameRound.dealerCardTurn += 1;
            }
            // var turn = Texas.GameRound.dealerCardTurn;
            // $card = $('#dealer_card' + turn);
            // Texas.GameRound.setCard(Texas.GameRound.dealerCards[i], $card);
            // Texas.GameRound.dealerCardTurn += 1;
        },

        setPlayerFunds: function (player_funds) {
            var funds = JSON.parse(player_funds);
            for (player in funds) {
                if (player.toString() === $('#current-player-id').val()) {
                    $('#txt_myfund').css('visibility', 'visible');
                    $('#my_fund').text(funds[player]);
                } else {
                    $('#txt_fund_' + player).css('visibility', 'visible')
                        .text("Stake: " + funds[player]);
                }
            }
        },

        gameOver: function (data) {
            Texas.Player.disableLastTurn();
            Texas.Player.disableBetMode();
            $('#pot').text("Pot: " + 0);
            $('#page_title').text(data.winner + " wins! Congratulations!");
        },

        newRound: function (data) {
            Texas.GameRound.roundId = data.round_id;

            // get cards info
            // var current_player = $("#current-player-id").val();
            // var my_player_cards = data.player_cards[current_player];
            var my_player_cards = data.player_cards;
            // set cards
            Texas.GameRound.setPlayerCards(my_player_cards);
            Texas.GameRound.setPlayerFunds(data.player_funds);
            $('#pot').css('visibility', 'visible');

            // var dealer_cards = data.dealer_cards.split(",");
            // Texas.GameRound.dealerCards = dealer_cards;
            // Texas.GameRound.dealerCardTurn = 3;
            // // show three dealer cards
            // Texas.GameRound.show3Cards(dealer_cards);
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
                    Texas.GameRound.turnoverCard(data);
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
            $('#btn_allin').css('visibility', 'hidden');
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
            currentPlayerId = $('#current-player-id').val();
            isCurrentPlayer = data.player.userid.toString() === currentPlayerId;


            if (isCurrentPlayer) {
                Texas.Player.enableBetMode(data);
            }
            // renew the pot
            $('#pot').text("Pot: " + data.pot);
            // disable last turn
            Texas.Player.disableLastTurn();
            // show previous bet's result
            // var prev_player = data.prev_player;
            // if (prev_player.id.toString() !== currentPlayerId) {
            //     $('#txt_fund_' + prev_player.id).text("Stake: " + prev_player.fund);
            //     if (prev_player.op === 'bets') {
            //         $('#txt_op_' + prev_player.id).text(prev_player.op + " " + prev_player.bet);
            //     } else {
            //         $('#txt_op_' + prev_player.id).text(prev_player.op);
            //     }
            // }
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
        players: [],
        seats: 0,
        availableSeat: 0,

        createPlayer: function ($seat, player) {
            var div1 = $('<div class="col-xs-12 col-sm-3 pull-left"><br></div>');
            div1.append($("<img>").attr({
                src: "/" + player.photo_src,
                alt: "",
                class: "img-circle img-player"
            }));
            div1.append($("<br>"));
            div1.append($("<span></span>").text(player.name));
            $seat.append(div1);
            var div2 = $('<div class="col-xs-12 col-sm-9 pull-right"><br></div>');
            div2.append($("<span></span>").attr({
                id: "txt_fund_" + player.id,
                class: "txt-fund"
            }));
            div2.append($("<br><br>"));
            div2.append($("<span></span>").attr({
                id: "txt_turn_" + player.id,
                class: "txt-turn"
            }));
            div2.append($("<br><br>"));
            div2.append($("<span></span>").attr({
                id: "txt_op_" + player.id,
                class: "txt-turn"
            }));
            $seat.append(div2);

        },

        initGame: function (data) {
            Texas.Game.gameNo = data.game_no;
            // initialize the room
            // set seats == player_num (decides by creator)
            // var player_num = data.player_num;
            var player_num = data.player_num;
            Texas.Game.seats = player_num - 1;
            var players = data.players;
            var current_player_id = $('#current-player-id').val();
            var order = 1;
            for (p in players) {
                player = players[p];
                if (player.id.toString() === current_player_id) {
                    order = parseInt(p) + 1;
                }
            }
            if (order !== 1) {
                Texas.Game.availableSeat = player_num - order;
            } else {
                Texas.Game.availableSeat = 0;
            }
            for (p in players) {
                player = players[p];
                if (player.id.toString() !== current_player_id) {
                    $seat = $('#player-' + Texas.Game.availableSeat);
                    Texas.Game.createPlayer($seat, player);
                    $seat.attr('seated-player-id', player.id);
                    Texas.Game.players.push(player.id);
                    if (Texas.Game.availableSeat === (Texas.Game.seats - 1)) {
                        Texas.Game.availableSeat = 0;
                    } else {
                        Texas.Game.availableSeat += 1;
                    }
                }
            }
            var seats = Texas.Game.seats;
            for (s = 0; s < seats; s++) {
                $seat = $('#player-' + s);
                if ($seat.attr('seated-player-id') == undefined) {
                    $seat.attr('seated-player-id', null);
                }
            }
        },

        onGameUpdate: function (data) {
            if (Texas.Game.gameNo === null) {
                Texas.Game.initGame(data)
            }

            var current_player_id = $("#current-player-id").val();
            switch (data.event) {
                case 'player-add':
                    playerId = data.player_id;
                    if (playerId.toString() !== current_player_id
                        && $.inArray(playerId, Texas.Game.players) === -1) {
                        for (p in data.players) {
                            if (data.players[p].id === playerId) {
                                player = data.players[p];
                            }
                        }
                        // for (i = 0; i < Texas.Game.seats; i++) {
                        //     $seat = $('#player-' + i);
                        //     if ($seat.attr('seated-player-id') == null) {
                        //         break;
                        //     }
                        // }
                        $seat = $('#player-' + Texas.Game.availableSeat);
                        Texas.Game.createPlayer($seat, player);
                        $seat.attr('seated-player-id', playerId);
                        Texas.Game.players.push(player.id);
                        if (Texas.Game.availableSeat === (Texas.Game.seats - 1)) {
                            Texas.Game.availableSeat = 0;
                        } else {
                            Texas.Game.availableSeat += 1;
                        }
                    }
                    break;

                case 'player-remove':
                    playerId = data.player_id;
                    for (i = 0; i < Texas.Game.seats; i++) {
                        $seat = $('#player-' + i);
                        var id = $seat.attr('seated-player-id');
                        if (id == playerId) {
                            $seat.empty();
                            $seat.attr('seated-player-id', null);
                        }
                    }
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
            var origin = parseInt($('#my_fund').val());
            var bet = parseInt($('#myRange').val());
            $('#my_fund').text(origin - bet);
            Texas.socket.send(JSON.stringify({
                'message_type': 'bet',
                'bet': bet,
                'round_id': Texas.GameRound.roundId
            }));
            Texas.Player.disableBetMode();
        });

        $('#btn_allin').click(function () {
            var origin = parseInt($('#my_fund').val());
            var bet = parseInt($('#myRange').val());
            $('#my_fund').text(origin - bet);
            Texas.socket.send(JSON.stringify({
                'message_type': 'bet',
                'bet': $('#myRange').val(),
                'round_id': Texas.GameRound.roundId
            }));
            Texas.Player.disableBetMode();
        });

        $('#exit').click(function () {
            Texas.socket.send(JSON.stringify({
                'message_type': 'exit'
            }));
        });
    }
};


$(document).ready(function () {
    Texas.init();
});
