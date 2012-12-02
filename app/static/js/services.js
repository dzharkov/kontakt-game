app.factory('socket', function ($rootScope) {
    var socket = io.connect('http://' + window.location.hostname +':8001');

    socket.on('connect', function() {
        var roomId = parseInt(document.getElementById('room-id').value, 10);
        var sessionKey = document.getElementById('session-key').value;
        socket.emit('login', sessionKey, roomId);
    });

    return {
        on: function (eventName, callback) {
            socket.on(eventName, function () {
                var args = arguments;
                $rootScope.$apply(function () {
                    callback.apply(socket, args);
                });
            });
        },
        emit: function (eventName, data, callback) {
            socket.emit(eventName, data, function () {
                var args = arguments;
                $rootScope.$apply(function () {
                    if (callback) {
                        callback.apply(socket, args);
                    }
                });
            })
        }
    };
});
