themes = {
  "default": {
      "name": "Default",
      "id": "default",
      "class": ""
  },
  "yotsuba": {
      "name": "Yotsuba",
      "id": "yotsuba",
      "class": "theme-yotsuba"
  },
  "yotsuba-b": {
      "name": "Yotsuba B",
      "id": "yotsubaB",
      "class": "theme-yotsuba-b"
  }
}
const currentTheme = localStorage.getItem('theme');
function changeTheme(theme, themes) {
  const body = document.body;
  for (x in themes) {
    if(themes[x]['id'] == theme) {
      body.className = '';
      if(themes[x]['class'] != '') {
        body.classList.add(themes[x]['class']);
        document.cookie = "theme="+themes[x]['class']+"; expires=Fri, 31 Dec 9999 23:59:59 GMT";
      } else {
        body.removeAttribute("class");
        document.cookie = "theme="+themes[x]['id']+"; expires=Fri, 31 Dec 9999 23:59:59 GMT";
      }      
      localStorage.setItem('theme', themes[x]['class']);
      
    }
  }
}
//set current theme as selected in the dropdown.

themeSelect = document.getElementById(getCookie("theme"));
if(themeSelect != null) {
  themeSelect.selected = 'selected'
}


//get cookie value
function getCookie(name) {
  var match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
  if (match) return match[2];
}