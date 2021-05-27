function showAuthor() {
  var container = document.getElementById("authorContainer");
  var button = document.getElementById("toggleAuthorBox");
  if (container.style.display === "none") {
    container.style.display = "block";
    button.style.display = "none";
  } else {
    container.style.display = "none";
  }
}
function dropdownFunction(a) {
  a.parentNode.getElementsByClassName("dropdown-content")[0].classList.toggle("showDropdown");
  console.log("button pressed")
}
window.onclick = function(event) {
  if (!event.target.classList.contains('dropdown-button-marker')) {
    console.log("clicked elsewhere")
    var dropdowns = document.getElementsByClassName("dropdown-content");
    var i;
    for (i = 0; i < dropdowns.length; i++) {
      var openDropdown = dropdowns[i];
      if (openDropdown.classList.contains('showDropdown')) {
        openDropdown.classList.remove('showDropdown');
      }
    }
  } else {
    console.log("clicked on dropdownbutton")
    console.log(event.target)
  }
}
