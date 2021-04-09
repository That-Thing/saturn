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