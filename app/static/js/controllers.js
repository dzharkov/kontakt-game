function InitSpinner(){
    var opts = {
        lines: 13, // The number of lines to draw
        length: 17, // The length of each line
        width: 4, // The line thickness
        radius: 14, // The radius of the inner circle
        corners: 1, // Corner roundness (0..1)
        rotate: 0, // The rotation offset
        color: '#fff', // #rgb or #rrggbb
        speed: 1, // Rounds per second
        trail: 60, // Afterglow percentage
        shadow: false, // Whether to render a shadow
        hwaccel: false, // Whether to use hardware acceleration
        className: 'spinner', // The CSS class to assign to the spinner
        zIndex: 2e9, // The z-index (defaults to 2000000000)
        top: 'auto', // Top position relative to parent in px
        left: 'auto' // Left position relative to parent in px
    };
    var target = document.getElementById('preloader');
    var spinner = new Spinner(opts).spin(target);
}

function CompareTwoUsers (u1, u2){
    if(u1.isMaster){
        return -1;
    }
    if(u2.isMaster) {
        return 1;
    }
    if(u1.hasContact && !u2.hasContact){
        return -1;
    }
    if(!u1.hasContact && u2.hasContact){
        return 1;
    }
    if(u1.isOnline && !u2.isOnline){
        return -1;
    }
    if(!u1.isOnline && u2.isOnline){
        return 1;
    }
    return u1.nickname < u2.nickname;
}

function AppCtrl($scope, socket, $timeout) {
    InitSpinner();

    $scope.messages = [];

    function EachUser(func){
        var users = $scope.users;
        for(var i = 0; i < users.length; i++){
            func.apply(users[i]);
        }
        func.apply($scope.currentUser);
    }

    function FindUserById(id){
        var user = $scope.users.findById(id);
        if (id === $scope.currentUserId) {
            user = $scope.currentUser;
        };
        return user;
    }

    function FindUserByContactId(contactId){
        var contactOwner = $scope.users.firstOrDefault($scope.currentUser, function(u){
            return u.contact !== undefined && u.contact.id === contactId;
        });
        return contactOwner;
    }

    function AddMessage(message){
        var user = FindUserById(message.author_id);
        if (user !== undefined) {            
            $scope.messages.push({author:user.name, text:message.text, time:message.text}); 
            // scroll chatbox
            var scrollDown = function() {
                var chat = document.getElementById("chatbox");
                chat.scrollTop = chat.scrollHeight;
            };
            $timeout(scrollDown, 100);
            
        };
    }

    function RemoveContactById(contactId) {
        var contactOwner = $scope.users.firstOrDefault($scope.currentUser, function(u){
            return u.contact !== undefined && u.contact.id === contactId;
        });
        contactOwner.removeContact();
        $scope.users.sort(CompareTwoUsers);
    }

    $scope.createContact = function(val, desc){
        var data = {
            'word': $scope.availableWordPart + val,
            'description': desc
        };
        socket.emit('contact_create', data);
    };

    $scope.acceptContact = function(contact){
        if(contact !== undefined){
            var fullGuess = $scope.availableWordPart+contact.guess;
            socket.emit('contact_accept', {'contact_id': contact.id, 'word' : fullGuess});
            contact.guess = '';
        }
    };

    $scope.breakContact = function(breakGuess, contact){
        var fullGuess = $scope.availableWordPart+breakGuess;
        var contactId = (contact !== undefined)?contact.id:$scope.currentContactId;
        socket.emit('contact_break', {'contact_id': contactId, 'word' : fullGuess});
        breakGuess = "";
    };

    $scope.startGame = function() {
        socket.emit('game_start', {});
    };

    $scope.proposeGameWord = function(word) {
        socket.emit('game_word_propose', { 'word' : word });
    };

    $scope.cancelContact = function() {
        if ($scope.currentUser.hasContact) {
            socket.emit('contact_cancel', { 'contact_id' : $scope.currentUser.contact.id });
        };
    };

    $scope.newMessage = "";
    $scope.sendChatMessage = function() {
        socket.emit('chat_message_send', { 'text' : $scope.newMessage });        
        $scope.newMessage = "";
    };

    $scope.switchNormal = function(){
        $scope.infoBarMode = "stats";
        $scope.showUserControls = true;
    };

    $scope.switchContact = function(){
        $scope.infoBarMode = "timer";
        $scope.showUserControls = false;
    };

    $scope.switchEndGame = function(){
        $scope.infoBarMode = "completed";
        $scope.showUserControls = false;
    };

    function switchCreateContact(){
        if($scope.currentUser.isMaster)
            return;
        $scope.infoBarMode = "createContact";
        $scope.showUserControls = true;
    }

    $scope.switchCreateContact = switchCreateContact;

    $scope.switchNormal();

    $scope.onTimeout = function(){
        $scope.secondsLeft--;
        if ($scope.secondsLeft > 0) {
            $timeout($scope.onTimeout,1000);
        }
    }

    // Socket listeners

    socket.on('login_result', function(data) {
        console.debug('login_result', data);
        if(data.result === 1){
            $scope.currentUserId = data.user_id;
        }
    });

    socket.on('reload', function() {
        window.location.reload();
    });

    socket.on('joined_user', function(data) {
        console.debug('joined_user', data);
        var joinedUser = $scope.users.first(function(u){
            return u.id === data.id;
        });
        if(joinedUser === undefined){
            joinedUser = new User(data);
            if(joinedUser.id !== $scope.currentUserId){
                $scope.users.push(joinedUser);
                $scope.users.sort(CompareTwoUsers);
            }
        }
        if(joinedUser.id === $scope.masterId){
            joinedUser.makeMaster();
        }
        joinedUser.isOnline = true;
        if(joinedUser.id !== $scope.currentUser.id)
            alertify.log("Пользователь "+joinedUser.name+" присоединился к нам :)");
    });

    socket.on('user_quit', function(data) {
        console.debug('user_quit', data);
        var whoQuit = $scope.users.first(function(u){
                return u.id === data.user_id;
            }
        );
        if(whoQuit !== undefined){
            alertify.log("Пользователь "+whoQuit.name+" ушёл от нас :(");
            whoQuit.isOnline = false;
        }
    });

    socket.on('game_error', function(data) {
        console.debug('game_error', data);
        alertify.error(data);
    });

    function AcceptedContact(data){
        //data = {contact_id:int}
        console.debug('accepted_contact', data);
        $scope.contactFrom = $scope.users.firstOrDefault($scope.currentUser, function(u){
            return u.contact !== undefined && u.contact.id === data.contact_id;
        });
        if(data.user_id === $scope.currentUser.id) {
            $scope.contactTo = $scope.currentUser;
        }
        else {
            $scope.contactTo = $scope.users.findById(data.user_id);
        }
        alertify.log("Есть контакт!");
        $scope.secondsLeft = data.seconds_left;
        $scope.currentContactId = data.contact_id;
        $scope.switchContact();
        $timeout($scope.onTimeout, 1000);
    }

    socket.on('accepted_contact', AcceptedContact);

    socket.on('broken_contact', function(data) {
        console.debug('broken_contact', data);
        RemoveContactById(data.contact_id);
        alertify.log("Контакт был разорван ведущим.");
        $scope.switchNormal();
    });

    socket.on('unsuccessful_contact_breaking', function(data) {
        console.debug('unsuccessful_contact_breaking', data);
        alertify.log("Неуспешная попытка разорвать контакт.");
    });

    socket.on('successful_contact_connection', function(data) {
        console.debug('successful_contact_connection', data);
        EachUser(function(){this.removeContact();});
        alertify.log("Контакт успешно завершился (слово - "+data.word+")!");
    });

    function GameComplete(data){
        console.debug('game_complete', data);
        EachUser(function(){this.removeContact();});
        $scope.availableWordPart = data.word;
        $scope.switchEndGame();
        var message = 'Игра успешно завершена! Было отгадано слово ' + data.word;
        alertify.log(message);
    }

    socket.on('game_complete', GameComplete);

    socket.on('next_letter_opened', function(data) {
        console.debug('next_letter_opened', data);
        var letter = data.letter;
        $scope.availableWordPart += letter;
        alertify.log("Открыта новая буква: " + letter);
        $scope.switchNormal();
    });

    socket.on('unsuccessful_contact_connection', function(data) {
        console.debug('unsuccessful_contact_connection', data);
        alertify.error("Неудачный контакт");
        $scope.switchNormal();
        RemoveContactById(data.contact_id);
    });

    socket.on('room_state_update', function(room_state) {
        console.debug('room_state_update', room_state);
        var game = room_state.game;
        var users = [];
        for(var i = 0; i < room_state.users.length; i++){
            var contactData = game.contacts.first(function(x){
                return x.author_id === room_state.users[i].id;
            });
            var user = new User(room_state.users[i], contactData);
            if(user.id === game.master_id){
                user.makeMaster();
            }
            if(user.id === $scope.currentUserId){
                $scope.currentUser = user;
            }
            else
            {
                users.push(user);
            }
        }

        users.sort(CompareTwoUsers);
        $scope.users = users;
        $scope.availableWordPart = game.available_word_part;
        $scope.wordLength = game.word_length;
        $scope.masterId = game.master_id;

        if(game.accepted_contact !== undefined){
            AcceptedContact(game.accepted_contact);
        }
        if(game.state === 'complete'){
            $scope.switchEndGame();
        }

        var messages = room_state.chat_messages;
        for (var i = 0; i < messages.length; i++) {
            var message = messages[i];
            AddMessage(message);
        };

        $scope.pageLoaded = true;
    });

    socket.on('master_selection_unsuccessful', function(data) {
        alertify.error('Не удалось выбрать ведущего');
    });

    socket.on('game_word_accepted', function(data) {
       alertify.log('Ваше слово - ' + data.word + ' принято, вы - кандидат на должность ведущего!');
    });

    socket.on('master_contender', function(data) {
        var user = FindUserById(data.user_id);
        alertify.log('Игрок ' + user.name + ' стал кандидатом на должность ведущего!');
    });

    socket.on('contact_creation', function(data) {
        var contact = data.contact;
        if (contact.author_id === $scope.currentUserId) {
            $scope.switchNormal();
            $scope.currentUser.addContact(contact);
        }
        else{
            var user = $scope.users.findById(contact.author_id);
            user.addContact(contact);
        }
        alertify.log('Новый контакт от пользователя' + contact.author_id + ' c текстом: ' + contact.desc);
    });

    socket.on('contact_canceled', function(data) {
        var author = FindUserByContactId(data.contact_id);
        RemoveContactById(data.contact_id);
        alertify.log('Игрок ' + author.name + ' отменил контакт');
    });

    socket.on('master_selection_started', function(data) {
        alertify.log(data.user_id + ' начал игру! Предлагаем свои слова, возможно вас выберут ведущим через ' + data.seconds_left + " секунд" );
    });

    socket.on('game_running', function(data) {
        var game = data.game;
        alertify.log('Игра началась! Ведущий ' + game.master_id + ', начало слова - ' + game.available_word_part + ', длина - ' + game.word_length);
    });

    socket.on('chat_message', function(data) {
        var message = data.msg;
        AddMessage(message);
    });

    socket.on('room_deleted', function(data) {
        alertify.log('Комната удалена');
        document.location.href = document.getElementById('room-list-url').value;
    });

    socket.on('room_private', function(data) {
        alertify.log('Комната стала закрытой');
        document.location.href = document.getElementById('room-list-url').value;
    });

    socket.on('room_kick', function(data) {
        alertify.log('Вас выгнали из комнаты');
        document.location.href = document.getElementById('room-list-url').value;
    });

    socket.on('disconnect', function() {
    });
}