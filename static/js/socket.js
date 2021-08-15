var socket = io.connect(location.protocol+'//'+document.domain+':'+location.port);

socket.on('replyEvent', function() {
    location.reload();
});