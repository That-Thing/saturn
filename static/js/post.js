markPost = function(id) {

    if (isNaN(id)) {
      return;
    }
  
    if (markedPosting && markedPosting.className === 'markedPost') {
      markedPosting.className = 'innerPost';
    }
  
    var container = document.getElementById(id);
  
    if (!container || container.className !== 'replyDiv') {
      return;
    }
  
    markedPosting = container.getElementsByClassName('innerPost')[0];
  
    if (markedPosting) {
      markedPosting.className = 'markedPost';
    }
  
};