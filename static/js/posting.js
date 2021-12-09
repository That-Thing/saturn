function showAuthor() {
  var container = document.getElementById("author-container");
  var button = document.getElementById("toggle-author-box");
  if (container.style.display === "none") {
    container.style.display = "block";
    button.style.display = "none";
  } else {
    container.style.display = "none";
  }
}
function dropdownFunction(a) {
  a.parentNode.getElementsByClassName("dropdown-content")[0].classList.toggle("show-dropdown");
}
window.onclick = function(event) {
  if (!event.target.classList.contains('dropdown-button-marker')) {
    var dropdowns = document.getElementsByClassName("dropdown-content");
    var i;
    for (i = 0; i < dropdowns.length; i++) {
      var openDropdown = dropdowns[i];
      if (openDropdown.classList.contains('show-dropdown')) {
        openDropdown.classList.remove('show-dropdown');
      }
    }
  }
}
//hide reply to thread
function hidePost(post, board) {
  postElement = document.getElementById(post);
  postElement.classList.add("hide");
  let hidden = JSON.parse(localStorage.getItem('hidden'));
  if(hidden == null) {
    hidden = [];
  }
  hidden.push(board+"/"+post);
  localStorage.setItem('hidden', JSON.stringify(hidden));
  var hiddenMenu = document.getElementById('hidden-menu-inner');
  var newPost = document.createElement("div");
  newPost.classList.add("hidden-entry");
  newPost.id = `hidden-${post}-${board}`;
  var newPostText = document.createElement("span");
  newPostText.innerHTML=`No. ${post}`
  var newPostDelete = document.createElement("i");
  newPostDelete.className = 'fas fa-times text-icon-l text-icon remove-hidden';
  newPostDelete.onclick = function(){removeHidden(post, board)};
  newPost.appendChild(newPostDelete);
  newPost.appendChild(newPostText);
  hiddenMenu.appendChild(newPost);
}
//hide entire thread
function hideThread(post, board) {
  postElement = document.getElementById(post);
  postElement.parentNode.classList.add("hide");
  let hidden = JSON.parse(localStorage.getItem('hidden'));
  if(hidden == null) {
    hidden = [];
  }
  hidden.push(hidden.push(board+"/"+post));
  localStorage.setItem('hidden', JSON.stringify(hidden));
  var hiddenMenu = document.getElementById('hidden-menu-inner');
  var newPost = document.createElement("div");
  newPost.classList.add("hidden-entry");
  newPost.id = `hidden-${post}-${board}`;
  var newPostText = document.createElement("span").innerHTML=`No. ${post}`;
  var newPostDelete = document.createElement("i");
  newPostDelete.className = 'fas fa-times text-icon-l text-icon remove-hidden';
  newPostDelete.onclick = function(){removeHidden(post, board)};
  newPost.appendChild(newPostDelete);
  newPost.appendChild(newPostText);
  hiddenMenu.appendChild(newPost);
}


//might need to just rewrite this completely unless I figure out how to access sql data using JS. 
function showHiddenMenu() {
  document.getElementById('hidden-menu').style.display = "block";
  dragElement(document.getElementById("hidden-menu"));
}
function closeHidden() {
  document.getElementById('hidden-menu').style.display = "none";
}

function dragElement(elmnt) {
  var pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
  if (document.getElementById(elmnt.id + "drag-header")) {
    /* if present, the header is where you move the DIV from:*/
    document.getElementById(elmnt.id + "drag-header").onmousedown = dragMouseDown;
  } else {
    /* otherwise, move the DIV from anywhere inside the DIV:*/
    elmnt.onmousedown = dragMouseDown;
  }

  function dragMouseDown(e) {
    e = e || window.event;
    e.preventDefault();
    // get the mouse cursor position at startup:
    pos3 = e.clientX;
    pos4 = e.clientY;
    document.onmouseup = closeDragElement;
    // call a function whenever the cursor moves:
    document.onmousemove = elementDrag;
  }

  function elementDrag(e) {
    e = e || window.event;
    e.preventDefault();
    // calculate the new cursor position:
    pos1 = pos3 - e.clientX;
    pos2 = pos4 - e.clientY;
    pos3 = e.clientX;
    pos4 = e.clientY;
    // set the element's new position:
    elmnt.style.top = (elmnt.offsetTop - pos2) + "px";
    elmnt.style.left = (elmnt.offsetLeft - pos1) + "px";
  }

  function closeDragElement() {
    /* stop moving when mouse button is released:*/
    document.onmouseup = null;
    document.onmousemove = null;
  }
}

//Hide all threads/posts that are marked as hidden in the session
function checkHidden() {
  let hidden = JSON.parse(localStorage.getItem('hidden'));
  if (hidden != null) {
    var threads = document.getElementsByClassName('thread');
    var posts = document.getElementsByClassName('replyDiv');
    for( i=0; i< threads.length; i++ ) {
      if (hidden.includes(threads[i].id)) {
        threads[i].classList.add("hide");  
      }
    }
    for( i=0; i< posts.length; i++ ) {
      if (hidden.includes(posts[i].id)) {
        posts[i].classList.add("hide");  
      }
    }
  }
}
checkHidden()

//Remove hidden thread or post
function removeHidden(id, board) {
  console.log(id);
  var hidden = JSON.parse(localStorage.getItem('hidden'));
  for( i=0; i < hidden.length; i++ ) {
    console.log(hidden[i]);
    if(hidden[i] != null && hidden[i].split("/")[1] == id && hidden[i].split("/")[0] == board) {
      hidden.splice(i,1);
    }
  }
  localStorage.setItem('hidden', JSON.stringify(hidden));
  document.getElementById(id).classList.remove('hide');
  document.getElementById(`hidden-${id}-${board}`).remove();
}

//Post deletion
function deletePrompt(post) {
  var children = post.parentNode.children;
  var password = prompt("Could not delete; Please input post password.");
  if (password === null) {
    return;
  }
  children['password'].value = password;
  children['delete'].click();
}
//User banning
function banPrompt(post, type) {
  var children = post.parentNode.children;
  var length = null;
  var reason = null;
  var message = null;
  length = prompt("Length (ex: 1y2m3d4h5)");
  reason = prompt("Enter a reason for ban (optional)");
  message = prompt("Message to append (optional)");
  if(type == "board") {
    children['length'].value = length;
    children['reason'].value = reason;
    children['message'].value = message;
    children['ban'].click();
  } else if (type == "global") {
    children['global-length'].value = length;
    children['global-reason'].value = reason;
    children['global-message'].value = message;
    children['global-ban'].click();
  };

}
//paste support
document.getElementById("authorForm").addEventListener('paste', e => {
  document.getElementById("file-input").files = e.clipboardData.files;
});