//mark post linked in url
function checkUrl() {
    var elements = document.getElementsByClassName('marked-post');
    while(elements.length > 0){
        elements[0].classList.remove('marked-post');
    }
    var splitUrl = window.location.href.split('#');
    if (splitUrl.length > 1) {
        if(splitUrl[1].charAt(0) == "q") {
            console.log(">>"+splitUrl[1].substring(1))
            document.getElementById("message").innerHTML = document.getElementById("message").innerHTML + ">>"+splitUrl[1].substring(1)+"\n";
        } else if(document.getElementById(splitUrl[1]) != null) {
            document.getElementById(splitUrl[1]).childNodes[1].className += " marked-post";
        }
    }
}
checkUrl();
window.addEventListener("hashchange", checkUrl);

//add reply to textarea
// function addReply(reply) {
//     document.getElementById("message").innerHTML = document.getElementById("message").innerHTML + ">>" + "\n"
// }