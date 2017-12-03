Texas = {

    socket: null,

    GameRound: {
        roundId: null,
        dealerCardTurn: null,
        start: true,

        setCard: function (card, $card, size) {
            if (size == "large") {
                width = 75;
                height = 125;
            } else if (size == "medium") {
                width = 45;
                height = 75;
            } else {
                width = 24;
                height = 40;
            }

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
                Texas.GameRound.setCard(player_cards[card], $card, "large");
            }
        },

        show3Cards: function (dealer_cards) {
            for (i = 0; i < 3; i++) {
                $card = $('#dealer_card' + i);
                Texas.GameRound.setCard(dealer_cards[i], $card, "large");
                $card.css('visibility', 'visible');
            }
        },

        showPlayerCard: function ($player, cards) {
            var div = $('<div></div>');
            div.addClass('card-show');
            for (i in cards) {
                $card = $('<img>');
                $card.addClass('card-medium');
                $card.addClass('card' + i);
                Texas.GameRound.setCard(cards[i], $card, "medium");
                div.append($card);
            }
            $player.append(div);
        },

        setOperationInvisible: function () {
            var players = Texas.Game.players;
            for (i in players) {
                $('#op' + players[i]).css('visibility', 'hidden');
            }
        },

        setChipsInvisible: function () {
            for (i = 0; i < 7; i++) {
                $('#stack-' + i).css('visibility', 'hidden');
            }
        },

        setAchipInvisible: function ($stack) {
            $stack.css('visibility', 'hidden');
        },

        setDealerCardsInvisible: function () {
            for (i = 0; i < 5; i++) {
                $('#dealer_card' + i).css('visibility', 'hidden');
            }
        },

        hidePlayerCards: function () {
            for (i in Texas.Game.players) {
                $('.seat[seated-player-id=' + Texas.Game.players[i] + '] .card-show').remove();
            }
        },

        turnoverCard: function (data) {
            var dealer_cards = data.dealer_cards;
            if (dealer_cards.length === 3) {
                Texas.GameRound.dealerCardTurn = 3;
                Texas.GameRound.show3Cards(dealer_cards);
            } else {
                var turn = Texas.GameRound.dealerCardTurn;
                $card = $('#dealer_card' + turn);
                Texas.GameRound.setCard(dealer_cards, $card, "large");
                $card.css('visibility', 'visible');
                Texas.GameRound.dealerCardTurn += 1;
            }
        },

        setPlayerFunds: function (player_funds) {
            var funds = JSON.parse(player_funds);
            for (player in funds) {
                if (player.toString() === $('#current-player-id').val()) {
                    $('#txt_myfund').css('visibility', 'visible');
                    $('#my_fund').text(funds[player]);
                } else {
                    $('#txt_fund_' + player)
                        .text("Stake: " + funds[player]);
                }
            }
        },

        gameOver: function (data) {
            Texas.GameRound.start = true;
            Texas.Player.disableTimer();
            Texas.Player.disableBetMode();
            Texas.GameRound.setChipsInvisible();
            // new form of showing winner!!!!!!!!!!!!!!!!!!!!!!!!!!!
            $('.font-win').text(data.winner + " wins!");
            $('.game-result').css('visibility', 'visible');
        },

        updatePlayer: function (data) {
            // show previous bet's result
            var currentPlayerId = $('#current-player-id').val();
            var prev_player = data.prev_player;
            if (prev_player.userid.toString() != currentPlayerId) {
                var userid = prev_player.userid;
                // set current fund
                $('#txt_fund_' + userid).text("Stake: " + prev_player.fund);
                Texas.Player.setPlayerOperation($('#op' + userid), prev_player.op);
                if (prev_player.op === 'bets') {
                    $('#bet' + userid).text("$" + prev_player.bet);
                    $('.stack[seated-player-id=' + userid + ']').css('visibility', 'visible');
                } else if (prev_player.op === 'folds') {
                    $('.seat[seated-player-id=' + userid + '] .player-img').css('opacity', '0.5');
                    $('.seat[seated-player-id=' + userid + '] .player-info').css('opacity', '0.5');
                    Texas.GameRound.setAchipInvisible($('.stack[seated-player-id=' + userid + ']'));
                }
            } else {
                $('#my_fund').text(prev_player.fund);
            }
        },

        resetUserOpacity: function () {
            var players = Texas.Game.players;
          for (p in players) {
              $('.seat[seated-player-id=' + players[p] + '] .player-img').css('opacity', '1');
              $('.seat[seated-player-id=' + players[p] + '] .player-info').css('opacity', '1');
          }
        },

        newRound: function (data) {
            Texas.GameRound.roundId = data.round_id;
            // start game in 5 seconds
            setTimeout(function () {
                $('.game-result').css('visibility', 'hidden');
                Texas.GameRound.setDealerCardsInvisible();
                Texas.GameRound.hidePlayerCards();
                Texas.GameRound.setOperationInvisible();
                Texas.GameRound.setChipsInvisible();
                Texas.GameRound.resetUserOpacity();
                // get cards info
                var my_player_cards = data.player_cards;
                // set cards
                Texas.GameRound.setPlayerCards(my_player_cards);
                // set funds
                Texas.GameRound.setPlayerFunds(data.player_funds);
                $('#pot').css('visibility', 'visible');
            }, 5000);
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
                case 'fund-update':
                    Texas.GameRound.updatePlayer(data);
                    break;
                case 'add-dealer-card':
                    Texas.GameRound.turnoverCard(data);
                    break;
                case 'game-over':
                    Texas.GameRound.gameOver(data);
                    break;
                case 'showdown':
                    Texas.Game.showPlayersCards(data);
                    break;
            }
        }
    },

    Player: {
        betMode: false,
        currPlayer: null,

        resetTimers: function () {
            $('#timer0').TimeCircles().destroy();
            var players = Texas.Game.players;
            for (p in players) {
                $('#timer' + players[p]).TimeCircles().destroy();
            }
        },

        enableBet: function (data) {
            var min = data.min_bet; // the minimum fund that a player should pay to bet
            var max = data.max_bet; // the maximum fund that a player is able to bet
            var money = data.player.money;
            // check available
            if (max - money == min) {
                $('#btn_check').removeAttr("disabled").removeClass('btn-disabled');
            }
            $('#btn_bet').removeAttr("disabled").removeClass('btn-disabled');
            $('#btn_fold').removeAttr("disabled").removeClass('btn-disabled');
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
            // // all in
            // if (min >= max) {
            //     $('#btn_fold').css('visibility', 'visible');
            //     $('#btn_allin').css('display', 'inline');
            // }
        },

        disableBet: function () {
            $('#btn_check').attr('disabled', 'disabled').addClass('btn-disabled');
            $('#btn_fold').attr('disabled', 'disabled').addClass('btn-disabled');
            $('#btn_bet').attr('disabled', 'disabled').addClass('btn-disabled');
            // $('#btn_allin').css('visibility', 'hidden');
            $('#chips').css('visibility', 'hidden');
        },

        enableBetMode: function (data) {
            Texas.Player.betMode = true;
            Texas.Player.enableBet(data);
            // set timer0
            Texas.Player.enableTimer($('#timer0'));
        },

        disableBetMode: function () {
            Texas.Player.betMode = false;
            Texas.Player.disableBet();
        },

        disableLastTurn: function () {
            if (Texas.Player.currPlayer !== null) {
                $('#timer' + Texas.Player.currPlayer).TimeCircles().destroy();
            }
        },

        disableTimer: function () {
            var currentPlayerId = $('#current-player-id').val();
            if (Texas.Player.currPlayer == currentPlayerId) {
                // disable current player's timer
                $('#timer0').TimeCircles().destroy();
            } else {
                $('#timer' + Texas.Player.currPlayer).TimeCircles().destroy();
            }
        },

        enableTimer: function ($timer) {
            $timer.TimeCircles({
                "start": true,
                "animation": "smooth",
                "bg_width": 2,
                "fg_width": 0.05,
                "count_past_zero": false,
                "total_duration": 30,
                "direction": "Counter-clockwise",
                "time": {
                    "Days": {show: false},
                    "Hours": {show: false},
                    "Minutes": {show: false},
                    "Seconds": {show: true}
                }
            }).addListener(countdownComplete);

            function countdownComplete(unit, value, total) {
                if (total <= 0) {
                    // fold
                    Texas.Player.fold();
                }
            }
        },

        fold: function () {
            Texas.socket.send(JSON.stringify({
                'message_type': 'bet',
                'bet': -1,
                'round_id': Texas.GameRound.roundId
            }));
            Texas.Player.disableBetMode();
            Texas.Player.disableTimer();
        },

        enableAction: function (data) {
            currentPlayerId = $('#current-player-id').val();
            isCurrentPlayer = data.player.userid.toString() === currentPlayerId;

            // renew the pot
            $('#pot').text("Pot: " + data.pot);
            // disable last turn
            Texas.Player.disableLastTurn();
            // enable this turn
            var currplayer = data.player.userid;
            Texas.Player.currPlayer = currplayer;
            if (isCurrentPlayer) {
                Texas.Player.enableBetMode(data);
            } else {
                // only set timers
                Texas.Player.enableTimer($('#timer' + currplayer));
            }
        },

        onPlayerAction: function (data) {
            if (Texas.GameRound.start) {
                setTimeout(function () {
                    Texas.Player.enableAction(data);
                }, 5000);
                Texas.GameRound.start = false;
            } else {
                Texas.Player.enableAction(data);
            }
        },

        setPlayerOperation: function ($op, type) {
            switch (type) {
                case "bets":
                    $op.css({
                        'background-color': '#408000',
                        width: '40px'
                    });
                    $op.text('Bet');
                    break;
                case "checks":
                    $op.css({
                        'background-color': '#993366',
                        width: '60px'
                    });
                    $op.text('Check');
                    break;
                case "folds":
                    $op.css({
                        'background-color': '#666666',
                        width: '50px'
                    });
                    $op.text('Fold');
                    break;
                case "allin":
                    $op.css({
                        'background-color': '#e6005c',
                        width: '50px'
                    });
                    $op.text('All in');
                    break;
            }
            $op.css('visibility', 'visible');
        }
    },

    Game: {
        gameNo: null,
        players: [],
        seats: 0,
        availableSeat: 0,

        createPlayer: function ($seat, player) {
            $seat.addClass("seat");
            $seat.attr('seated-player-id', player.id);
            var div1 = $('<div></div>');
            div1.addClass('player-img');
            div1.append($("<img>").attr({
                src: "/" + player.photo_src,
                alt: "", // add a photo as alternative
                class: "img-circle img-player"
            }));
            $seat.append(div1);
            var div2 = $('<div></div>').attr({
                id: "timer" + player.id,
                class: "timer",
                "data-timer": 30
            });
            $seat.append(div2);
            var div3 = $('<div></div>').attr({class: "player-info"});
            div3.append($("<span></span>").text(player.name));
            div3.append($("<br>"));
            div3.append($("<span></span>").attr({
                id: "txt_fund_" + player.id
            }).text("Stack: " + player.money));
            $seat.append(div3);
            var div4 = $('<div></div>').attr({
                class: "operation",
                id: "op" + player.id
            });
            $seat.append(div4);
            $seat.css('visibility', 'visible');
        },

        setBetChips: function ($stack, player) {
            $stack.addClass("stack");
            $stack.append($("<img>").attr({
                src: "/static/media/default/chip_default.png",
                alt: "",
                class: "chip"
            }));
            var div = $('<div></div>').attr({class: 'chip-info'});
            div.append($("<span></span>").attr({id: "bet" + player.id}));
            $stack.append(div);
            $stack.attr('seated-player-id', player.id);
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
            // find my order
            for (i = 0; i < players.length; i++) {
                if (players[i].id == current_player_id) {
                    my_order = i;
                }
            }
            for (p = 0; p < players.length; p++) {
                var player = players[p];
                if (p == my_order) {
                    $('#txt_myfund').css('visibility', 'visible');
                    $('#my_fund').text(player.money);
                    continue;
                } else if (p < my_order) {
                    order = p + 7 - my_order;
                } else {
                    order = p - my_order - 1;
                }
                $seat = $('#player-' + order);
                Texas.Game.createPlayer($seat, player);
                $stack = $('#stack-' + order);
                Texas.Game.setBetChips($stack, player);
                Texas.Game.players.push(player.id);
            }
            Texas.Game.availableSeat = p - my_order - 1;
            for (s = 0; s < 7; s++) {
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
                        && $.inArray(playerId.toString(), Texas.Game.players) === -1) {
                        for (p in data.players) {
                            if (data.players[p].id === playerId.toString()) {
                                player = data.players[p];
                            }
                        }
                        var available_seat = Texas.Game.availableSeat;
                        $seat = $('#player-' + available_seat);
                        Texas.Game.createPlayer($seat, player);
                        $stack = $('#stack-' + available_seat);
                        Texas.Game.setBetChips($stack, player);
                        Texas.Game.players.push(player.id);
                        for (i = 0; i < 7; i++) {
                            available_seat = (available_seat + 1) % 7;
                            if ($('#player-' + available_seat).attr('seated-player-id') == null) {
                                Texas.Game.availableSeat = available_seat;
                                break;
                            }
                        }
                    }
                    break;

                case 'player-remove':
                    playerId = data.player_id;
                    $seat = $('.seat[seated-player-id=' + data.player_id + ']');
                    $seat.empty();
                    $seat.attr('seated-player-id', null);
                    $stack = $('.stack[seated-player-id=' + data.player_id + ']');
                    $stack.empty();
                    $stack.attr('seated-player-id', null);
                    Texas.Game.players.splice($.inArray(playerId, Texas.Game.players), 1);
                    break;
            }
        },

        showPlayersCards: function (data) {
            var cards = JSON.parse(data.cards);
            for (i in cards) {
                var userid = cards[i].id;
                var card = cards[i].card;
                Texas.GameRound.showPlayerCard($('.seat[seated-player-id=' + userid + ']'), card);
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
            Texas.Player.disableTimer();
        });

        $('#btn_fold').click(function () {
            Texas.Player.fold();
        });

        $('#btn_bet').click(function () {
            // var origin = parseInt($('#my_fund').text());
            var bet = parseInt($('#myRange').val());
            // $('#my_fund').text(origin - bet);
            Texas.socket.send(JSON.stringify({
                'message_type': 'bet',
                'bet': bet,
                'round_id': Texas.GameRound.roundId
            }));
            Texas.Player.disableBetMode();
            Texas.Player.disableTimer();
        });

        $('#btn_allin').click(function () {
            // var origin = parseInt($('#my_fund').text());
            // var bet = parseInt($('#myRange').val());
            // $('#my_fund').text(origin - bet);
            Texas.socket.send(JSON.stringify({
                'message_type': 'bet',
                'bet': -2,
                'round_id': Texas.GameRound.roundId
            }));
            Texas.Player.disableBetMode();
            Texas.Player.disableTimer();
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
