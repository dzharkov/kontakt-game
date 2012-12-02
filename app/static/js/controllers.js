function AppCtrl($scope, socket) {
    var CompareTwoUsers = function(u1, u2){
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


    // Socket listeners

    socket.on('login_result', function(login_result) {
        $scope.currentUserId = login_result;
    });

    socket.on('reload', function() {
        window.location.reload();
    });

    socket.on('joined_user', function(userData) {
        console.debug('joined_user', userData);
        var joinedUser = $scope.users.firstOrUndefined(function(u){
            return u.id === userData.id;
        });
        if(joinedUser === undefined){
            joinedUser = new User(userData);
            $scope.users.push(joinedUser);
            $scope.users.sort(CompareTwoUsers);
        }
        if(joinedUser.id === $scope.masterId){
            joinedUser.makeMaster();
        }
        joinedUser.isOnline = true;
        alertify.success("Пользователь "+joinedUser.name+" присоединился к нам :)");
    });

    socket.on('user_quit', function(id) {
        var whoQuit = $scope.users.firstOrUndefined(function(u){
                return u.id === id;
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
    });

    socket.on('broken_contact', function(data) {
        console.debug('broken_contact', data);
    });

    socket.on('unsuccessful_contact_breaking', function(data) {
        console.debug('unsuccessful_contact_breaking', data);
    });

    socket.on('successful_contact_connection', function(data) {
        console.debug('successful_contact_connection', data);
    });

    socket.on('game_complete', function(data) {
        console.debug('game_complete', data);
    });

    socket.on('next_letter_opened', function(data) {
        var letter = data.letter;
        $scope.availableWordPart += letter;
        alertify.success("Открыта новая буква: " + letter + "!");
    });

    socket.on('unsuccessful_contact_connection', function(data) {
        console.debug('unsuccessful_contact_connection', data);
    });

    socket.on('room_state_update', function(room_state) {
        console.debug('room_state_update', room_state);
        var game = room_state.game;
        var users = [];
        for(var i = 0; i < room_state.users.length; i++){
            var contactData = game.contacts.firstOrUndefined(function(x){
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

    $scope.createContact = function(){

    };

    $scope.acceptContact = function(contact){
        if(contact !== undefined){
            var fullGuess = $scope.availableWordPart+contact.guess;
            socket.emit('contact_accept', {'contact_id': contact.id, 'word' : fullGuess});
            contact.guess = '';
        }
    };
}