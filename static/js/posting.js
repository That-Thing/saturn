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
  let hidden = sessionStorage.getItem('hidden')
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
  let hidden = sessionStorage.getItem('hidden')
  if (hidden == null) {
    hidden = "";
  }
  console.log(hidden)
  hidden = hidden + ","+post.id;
  sessionStorage.setItem('hidden', hidden)
}