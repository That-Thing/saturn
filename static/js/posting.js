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

function hidePostReply(post) {
  post = post.parentNode.parentNode.parentNode.parentNode.parentNode;//this is such a stupid way of doing this.
  post.classList.add("hide");
  console.log(post.id)
  let hidden = sessionStorage.getItem('hidden');
  if (hidden == null) {
    hidden = "";
  }
  hidden = hidden + ","+post.id;
  sessionStorage.setItem('hidden', hidden)
  console.log(hidden)
}
function hidePostThread(post) {
  post = post.parentNode.parentNode.parentNode.parentNode.parentNode;
  console.log(post.id)
  post.classList.add("hide");
  let hidden = sessionStorage.getItem('hidden');
  if (hidden == null) {
    hidden = "";
  }
  console.log(hidden)
  hidden = hidden + ","+post.id;
  sessionStorage.setItem('hidden', hidden)
}


//might need to just rewrite this completely unless I figure out how to access sql data using JS. 
//Don't know if this even works.
function showHiddenMenu() {
  var hiddenMenu = document.createElement("div");
  hiddenMenu.className = "floating-menu";
  hiddenMenu.id = "hidden-menu";
  try {
    var hidden = sessionStorage.getItem('hidden').replace('t-','');
  } catch (e) {
    var hidden;
  }
  try {
    hidden = hidden.split(",");
  } catch (e) {
    //do nothing
  }
  var divs = "";
  try {
    hidden.forEach(element => {
      console.log(element)
      if (element != null && element != undefined) {
        //No need for null in the array
        divs = divs + '<div class="hidden-entry" id="hidden-'+ element +'"><span>'+ element +'</span> <i class="fas fa-times text-icon-l remove-hidden" onclick="removeHidden(this)"></i></div><br>';
      }
    });
  } catch {
    //do nothing...again
  }
  menuTemplate = `
    <div class="drag-header floating-menu-header">
        <label>Hidden Posts</label>
        <i class="fas fa-times text-icon text-icon-l close-menu"></i>
    </div>
    <div class="floating-menu-inner">
  ` + divs +  `
    </div>
  `;
  hiddenMenu.innerHTML = menuTemplate;
  document.body.appendChild(hiddenMenu);
  dragElement(document.getElementById("hidden-menu"));
}
//dragElement(document.getElementById("mydiv"));

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