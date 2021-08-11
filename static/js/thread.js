function checkUrl() {
    var elements = document.getElementsByClassName('marked-post');
    while(elements.length > 0){
        elements[0].classList.remove('marked-post');
    }
    var splitUrl = window.location.href.split('#');
    if (splitUrl.length > 1) {
        if(document.getElementById(splitUrl[1]) != null) {
            document.getElementById(splitUrl[1]).childNodes[1].className += " marked-post";
        }
    }
}
checkUrl();
window.addEventListener("hashchange", checkUrl);
function reply(post) {
    document.getElementById("comment").innerHTML += ">>" + post.text + "\n";
}
window.onload = function() {
    var splitUrl = window.location.href.split('#');
    if (splitUrl[1] && splitUrl[1].charAt(0) == "q") {
        document.getElementById("comment").innerHTML += ">>" + splitUrl[1].substring(1) + "\n";
    }
}