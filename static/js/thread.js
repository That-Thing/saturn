//mark post linked in url
function markPost() {
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
markPost();
window.addEventListener("hashchange", markPost);