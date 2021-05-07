// JS function to convert BBCode and HTML code - http;//coursesweb.net/javascript/
//Not mine. I suck at JS
var BBCodeHTML = function() {
    var me = this;
    var token_match = /{[A-Z_]+[0-9]*}/ig;
    var tokens = {
      'URL' : '((?:(?:[a-z][a-z\\d+\\-.]*:\\/{2}(?:(?:[a-z0-9\\-._~\\!$&\'*+,;=:@|]+|%[\\dA-F]{2})+|[0-9.]+|\\[[a-z0-9.]+:[a-z0-9.]+:[a-z0-9.:]+\\])(?::\\d*)?(?:\\/(?:[a-z0-9\\-._~\\!$&\'*+,;=:@|]+|%[\\dA-F]{2})*)*(?:\\?(?:[a-z0-9\\-._~\\!$&\'*+,;=:@\\/?|]+|%[\\dA-F]{2})*)?(?:#(?:[a-z0-9\\-._~\\!$&\'*+,;=:@\\/?|]+|%[\\dA-F]{2})*)?)|(?:www\\.(?:[a-z0-9\\-._~\\!$&\'*+,;=:@|]+|%[\\dA-F]{2})+(?::\\d*)?(?:\\/(?:[a-z0-9\\-._~\\!$&\'*+,;=:@|]+|%[\\dA-F]{2})*)*(?:\\?(?:[a-z0-9\\-._~\\!$&\'*+,;=:@\\/?|]+|%[\\dA-F]{2})*)?(?:#(?:[a-z0-9\\-._~\\!$&\'*+,;=:@\\/?|]+|%[\\dA-F]{2})*)?)))',
      'LINK' : '([a-z0-9\-\./]+[^"\' ]*)',
      'EMAIL' : '((?:[\\w\!\#$\%\&\'\*\+\-\/\=\?\^\`{\|\}\~]+\.)*(?:[\\w\!\#$\%\'\*\+\-\/\=\?\^\`{\|\}\~]|&)+@(?:(?:(?:(?:(?:[a-z0-9]{1}[a-z0-9\-]{0,62}[a-z0-9]{1})|[a-z])\.)+[a-z]{2,6})|(?:\\d{1,3}\.){3}\\d{1,3}(?:\:\\d{1,5})?))',
      'TEXT' : '(.*?)',
      'SIMPLETEXT' : '([a-zA-Z0-9-+.,_ ]+)',
      'INTTEXT' : '([a-zA-Z0-9-+,_. ]+)',
      'IDENTIFIER' : '([a-zA-Z0-9-_]+)',
      'COLOR' : '([a-z]+|#[0-9abcdef]+)',
      'NUMBER'  : '([0-9]+)'
    };  
    var bbcode_matches = [];
    var html_tpls = [];
    var html_matches = [];   
    var bbcode_tpls = [];
    var _getRegEx = function(str) {
      var matches = str.match(token_match);
      var nrmatches = matches.length;
      var i = 0;
      var replacement = '';
      if (nrmatches <= 0) {
        return new RegExp(preg_quote(str), 'g');
      }
      for(; i < nrmatches; i += 1) {
        var token = matches[i].replace(/[{}0-9]/g, '');
  
        if (tokens[token]) {
          replacement += preg_quote(str.substr(0, str.indexOf(matches[i]))) + tokens[token];
          str = str.substr(str.indexOf(matches[i]) + matches[i].length);
        }
      }
      replacement += preg_quote(str);
      return new RegExp(replacement, 'gi');
    };
    var _getTpls = function(str) {
      var matches = str.match(token_match);
      var nrmatches = matches.length;
      var i = 0;
      var replacement = '';
      var positions = {};
      var next_position = 0;
  
      if (nrmatches <= 0) {
        return str;
      }
      for(; i < nrmatches; i += 1) {
        var token = matches[i].replace(/[{}0-9]/g, '');
        var position;
        if (positions[matches[i]]) {
          position = positions[matches[i]];
        } else {
          next_position += 1;
          position = next_position;
          positions[matches[i]] = position;
        }
  
        if (tokens[token]) {
          replacement += str.substr(0, str.indexOf(matches[i])) + '$' + position;
          str = str.substr(str.indexOf(matches[i]) + matches[i].length);
        }
      }
      replacement += str;
      return replacement;
    };
    me.bbcodeToHtml = function(str) {
      var nrbbcmatches = bbcode_matches.length;
      var i = 0;
      for(; i < nrbbcmatches; i += 1) {
        str = str.replace(bbcode_matches[i], html_tpls[i]);
      }
      return str;
    };
    function preg_quote (str, delimiter) {
      return (str + '').replace(new RegExp('[.\\\\+*?\\[\\^\\]$(){}=!<>|:\\' + (delimiter || '') + '-]', 'g'), '\\$&');
    }
    me.addFormat = function(bbcode_match, bbcode_tpl) {
        bbcode_matches.push(_getRegEx(bbcode_match));
        html_tpls.push(_getTpls(bbcode_tpl));
        html_matches.push(_getRegEx(bbcode_tpl));
        bbcode_tpls.push(_getTpls(bbcode_match));
      };
    me.addFormat('[b]{TEXT}[/b]', '<strong>{TEXT}</strong>'); //bold
    me.addFormat('[i]{TEXT}[/i]', '<em>{TEXT}</em>'); //italics
    me.addFormat('[u]{TEXT}[/u]', '<u>{TEXT}</u>'); //underlined
    me.addFormat('[s]{TEXT}[/s]', '<s>{TEXT}</s>'); //strikethrough
    // me.addFormat('[color=COLOR]{TEXT}[/color]', '<span style="{COLOR}">{TEXT}</span>'); //colored text
    // me.addFormat('[highlight={COLOR}]{TEXT}[/highlight]', '<span style="background-color:{COLOR}">{TEXT}</span>'); //highlighted text
    me.addFormat('[spoiler]{TEXT}[/spoiler]', '<span class="spoiler">{TEXT}</span>'); //spoiler
    me.addFormat('[code]{TEXT}[/code]', '<code>{TEXT}</code>'); //code
    me.addFormat('*{TEXT}*', '<em>{TEXT}</em>'); //alternative italics
    me.addFormat('**{TEXT}**', '<strong>{TEXT}</strong>'); //alternative bold
    me.addFormat('__{TEXT}__', '<u>{TEXT}</u>'); //alternative underline
    me.addFormat('~~{TEXT}~~', '<s>{TEXT}</s>'); //alternative strikethrough
    me.addFormat('||{TEXT}||', '<span class="spoiler">{TEXT}</span>'); //alternative spoiler
    me.addFormat('##{TEXT}##', '<span class="rainbow">{TEXT}</span>'); //rainbow text
    me.addFormat('((({TEXT})))', '<span class="detected">{TEXT}</span>'); //detected text
    me.addFormat('=={TEXT}==', '<span class="redText">{TEXT}</span>'); //red text
  };
  var textParser = new BBCodeHTML();

//checks if given string is greentext. 
function checkGreentext(str) {
  const regex = /^>.*$/gm;
  let m;
  while ((m = regex.exec(str)) !== null) {
    if (m.index === regex.lastIndex) {
        regex.lastIndex++;
    }
    if(m.length > 0) {
        return true;
    }
  }
}
function checkPinktext(str) {
  const regex = /^<.*$/gm;
  let m;
  while ((m = regex.exec(str)) !== null) {
    if (m.index === regex.lastIndex) {
        regex.lastIndex++;
    }
    if(m.length > 0) {
        return true;
    }
  }
}
function formatText() {
    var posts = document.getElementsByClassName("comment");
    for (var i = 0; i < posts.length; i++) {
        var text = posts[i].textContent;
        posts[i].innerHTML=textParser.bbcodeToHtml(text);
        lines = text.match(/[^\r\n]+/g);
        console.log(lines)
        for (var x = 0; x < lines.length; x++) { //this is an incredibly broken and stupid way to do this. For anyone using this code as an example..DON'T
          if(checkPinktext(lines[x]) == true) {
            lines[x] = lines[x].substring(1);
            lines[x] = "<span class='pinktext'>&lt;"+lines[x]+"</span>"
          }
          if(checkGreentext(lines[x]) == true) {
            lines[x] = "<span class='greentext'>"+lines[x]+"</span>"
          }
        }
        posts[i].innerHTML = lines.join("\n")

    }
};
formatText();


