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
function hidePostReply(post) {
  post = post.parentNode.parentNode.parentNode.parentNode.parentNode;//this is such a stupid way of doing this.
  post.classList.add("hide");
  let hidden = JSON.parse(localStorage.getItem('hidden'));
  if(hidden == null) {
    hidden = [];
  }
  hidden.push(post.id);
  localStorage.setItem('hidden', JSON.stringify(hidden))
}
//hide entire thread
function hidePostThread(post) {
  post = post.parentNode.parentNode.parentNode.parentNode.parentNode;
  post.classList.add("hide");
  let hidden = JSON.parse(localStorage.getItem('hidden'));
  if(hidden == null) {
    hidden = [];
  }
  hidden.push(post.id);
  localStorage.setItem('hidden', JSON.stringify(hidden))
}


//might need to just rewrite this completely unless I figure out how to access sql data using JS. 
function showHiddenMenu() {
  var hiddenMenu = document.createElement("div");
  hiddenMenu.className = "floating-menu";
  hiddenMenu.id = "hidden-menu";
  let hidden = JSON.parse(localStorage.getItem('hidden'));
  if(hidden == null) {
    hidden = [];
  }
  var divs = "";
  try {
    hidden.forEach(element => {
      if (element != null && element != undefined) {
        divs = divs + '<div class="hidden-entry" id="hidden-'+ element +'"><span>'+ element +'</span> <i class="fas fa-times text-icon-l remove-hidden" onclick="removeHidden(this)"></i></div><br>';
      }
    });
  } catch {
    //do nothing
  }
  menuTemplate = `
    <div class="drag-header floating-menu-header">
        <label>Hidden Posts</label>
        <i class="fas fa-times text-icon text-icon-l close-menu" onclick='closeHidden()'></i>
    </div>
    <div class="floating-menu-inner">
  ` + divs +  `
    </div>
  `;
  hiddenMenu.innerHTML = menuTemplate;
  document.body.appendChild(hiddenMenu);
  dragElement(document.getElementById("hidden-menu"));
}
function closeHidden() {
  document.getElementById("hidden-menu").remove();
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
function removeHidden(id) {
  document.getElementById(id.parentNode.remove());
  id = id.parentNode.id.replace('hidden-','');
  var hidden = JSON.parse(localStorage.getItem('hidden'));
  for( i=0; i< hidden.length; i++ ) {
    if(hidden[i] == id) {
      delete hidden[i]
    }
  }
  localStorage.setItem('hidden', JSON.stringify(hidden));
  document.getElementById(id).classList.remove('hide');
}

//TODO:
//Add a letter for board URI so it doesn't hide threads on other boards with the same number.



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

//paste support
document.getElementById("authorForm").addEventListener('paste', e => {
  document.getElementById("file-input").files = e.clipboardData.files;
});