function search(node) {
  if (!node) return;
  if ((node.previousSibling == null ||
          node.previousSibling.tagName == 'DIV' ||
          node.previousSibling.tagName == 'BR') && 
          node.nodeType == 3 && greentextRegex.test(node.textContent) &&
          !node.parentNode.isContentEditable  &&
          node.parentNode.tagName      != 'A' &&
          node.parentNode.tagName      != 'S' &&
          node.parentNode.className    != 'greentext' &&
          node.parentNode.className    != 'quote' ) {
          greenTxt(node);
  } else if(node.hasChildNodes()){
      for (var i = 0; i < node.childNodes.length; i++) {
          search(node.childNodes[i]);
      }
  }
}
var greentextRegex = /^\s*(?:>|&gt;)(?:[^<.>_]|>+[^>\s]+)/i;
function greenTxt(node) {
  var greenSpan;
  if (node.previousSibling != null && node.previousSibling.className == "greentext") {
      greenSpan = node.previousSibling;
  } else {
      greenSpan = document.createElement('span');
      greenSpan.setAttribute('class', 'greentext'); 
      node.parentNode.insertBefore(greenSpan, node);
  }
  greenSpan.appendChild(node);
  if (greenSpan.nextSibling != null &&
      (greenSpan.nextSibling.nodeType != 1 ||
      greenSpan.nextSibling.tagName != 'DIV' && 
      greenSpan.nextSibling.tagName != 'BR')) {
          greenTxt(greenSpan.nextSibling);
  }
}