function AppCtrl($scope, socket, $timeout) {
    function CompareTwoUsers (u1, u2){
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

    function deleteContact(contactId) {
        var contactOwner = $scope.users.firstOrDefault($scope.currentUser, function(u){
            return u.contact !== undefined && u.contact.id === contactId;
        });
        contactOwner.removeContact(contactId);
    }

    $scope.createContact = function(){

    };

    $scope.acceptContact = function(contact){
        if(contact !== undefined){
            var fullGuess = $scope.availableWordPart+contact.guess;
            socket.emit('contact_accept', {'contact_id': contact.id, 'word' : fullGuess});
            contact.guess = '';
        }
    };

    $scope.breakContact = function(breakGuess){
        var fullGuess = $scope.availableWordPart+breakGuess;
        socket.emit('contact_break', {'contact_id': $scope.currentContactId, 'word' : fullGuess});
        breakGuess = "";
    };

    function switchNormal(){
        $scope.infoBarMode = "stats";
        $scope.showUserControls = true;
    }

    function switchContacting(){
        $scope.infoBarMode = "timer";
        $scope.showUserControls = false;
    }

    switchNormal();

    $scope.modes = {"contacting":"timer", "normal":"stats"};

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
    });

    socket.on('accepted_contact', function(data) {
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
        $scope.secondsLeft = data.seconds_left;
        $scope.currentContactId = data.contact_id;
        switchContacting();
        $timeout($scope.onTimeout, 1000);
    });

    socket.on('broken_contact', function(data) {
        console.debug('broken_contact', data);
        deleteContact(data.contact_id);
        alertify.log("Контакт был разорван ведущим.");
        switchNormal();
    });

    socket.on('unsuccessful_contact_breaking', function(data) {
        console.debug('unsuccessful_contact_breaking', data);
        alertify.log("Неуспешная попытка разорвать контакт.");
    });

    socket.on('successful_contact_connection', function(data) {
        console.debug('successful_contact_connection', data);
        deleteContact(data.contact_id);
        alertify.log("Контакт успешно завершился (слово - "+data.word+")!");
    });

    socket.on('game_complete', function(data) {
        console.debug('game_complete', data);
        var message = 'Игра успешно завершена! Было отгадано слово ' + data.word;
        alertify.log( message, function () {
            // after clicking OK
        });
    });

    socket.on('next_letter_opened', function(data) {
        console.debug(data);
        var letter = data.letter;
        $scope.availableWordPart += letter;
        alertify.log("Открыта новая буква: " + letter + "!");
        switchNormal();
    });

    socket.on('unsuccessful_contact_connection', function(data) {
        console.debug('unsuccessful_contact_connection', data);
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
    });

    socket.on('disconnect', function() {
    });
}