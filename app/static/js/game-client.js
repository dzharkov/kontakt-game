
var conn;
function open_websocket(){

var show_message = function(message){
    var el = document.createElement('div');
    el.innerHTML = message;
    document.body.appendChild(el);
};

var roomId = parseInt(document.getElementById('room-id').value, 10);
var sessionKey = document.getElementById('session-key').value;

conn = io.connect('http://' + window.location.hostname +':8001');

conn.on('login_result', function(data) {
    console.debug('login_result', data);
    });

conn.on('reload', function() {
    window.location.reload();
    });

conn.on('joined_user', function(data) {
    console.debug('joined_user', data);
    });

conn.on('user_quit', function(data) {
    console.debug('user_quit', data);
    });

conn.on('game_error', function(data) {
    console.debug('game_error', data);
    });

conn.on('accepted_contact', function(data) {
    console.debug('accepted_contact', data);
    });

conn.on('broken_contact', function(data) {
    console.debug('broken_contact', data);
    });

conn.on('unsuccessful_contact_breaking', function(data) {
    console.debug('unsuccessful_contact_breaking', data);
    });

conn.on('successful_contact_connection', function(data) {
    console.debug('successful_contact_connection', data);
    });

conn.on('game_complete', function(data) {
    console.debug('game_complete', data);
    });

conn.on('next_letter_opened', function(data) {
    console.debug('next_letter_opened', data);
    });

conn.on('unsuccessful_contact_connection', function(data) {
    console.debug('unsuccessful_contact_connection', data);
    });

conn.on('connect', function() {
    show_message('connected');
    conn.emit('login', sessionKey, roomId);
});

conn.on('room_state_update', function(obj) {
    console.debug('room_state_update', obj);
    });

conn.on('disconnect', function() {
    show_message('disconnected');
    });
}