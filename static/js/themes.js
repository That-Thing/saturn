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
console.log(currentTheme)
function changeTheme(theme, themes) {
  const body = document.body;
  console.log("Selected theme: "+ theme)
  for (x in themes) {
    if(themes[x]['id'] == theme) {
      body.className = '';
      body.classList.add(themes[x]['class']);
      localStorage.setItem('theme', themes[x]['class']);
    }
  }
}

