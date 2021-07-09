//mark post linked in url
var splitUrl = window.location.href.split('#');
if (splitUrl.length > 1) {
    if(document.getElementById(splitUrl[1]) != null) {
        document.getElementById(splitUrl[1]).childNodes[1].className += " marked-post";
    }
}

