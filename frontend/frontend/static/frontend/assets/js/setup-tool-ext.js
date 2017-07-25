(function(){

// skip non setup page
if (!document.location.href.match('https?://[^/]+/[^/]+/setup\?.+'))
    return;

function init_tool(pathes) {
}

function check_pathes(pathes) {
}

var _config = null;
var _active = false;

function updateUI(config) {
  console.log(config);
  _config = config;

  $('#ste-parent').val(config[0]);
  ['title', 'description', 'link'].forEach(function(name){
      $('#ste-'+ name).val(name in config[1] ? config[1][name] : '');
  });
}

function showIcon(show) {
    $("#st-ext-trigger")[0].style.display = show ? "inline-block" : "none";
}

function changed() {
    var ch = false;
    if (_config[0] != $('#ste-parent').val())
        ch = true;
    ['title', 'description', 'link'].every(function(name){
        if (name in _config[1]) {
            if (_config[1][name] != $('#ste-'+ name).val())
                ch = true;
        }
        else
            ch = $('#ste-'+ name).val() != '';
        return !ch;
    });

    return ch;
}

function active() {
    return _active;
}

window.ET = {
    'showIcon': showIcon,
    'init': init_tool,
    'check': check_pathes,
    'updateUI': updateUI,
    'active': active
};

function show_ext(show) {
    if (show && changed() && !confirm($("#st-clicker-trigger").attr('confirm-text')))
        return;
    $("#st-ext-trigger")[0].style.display = show ? "inline-block" : "none";
    $("#st-clicker-trigger")[0].style.display = !show ? "inline-block" : "none";
    $("#st-extended")[0].style.display = !show ? "block" : "none";
    $("#st-clicker")[0].style.display = show ? "block" : "none";
    
    _active = show;
}

$(document).ready(function(){
    $("#st-ext-trigger").click(function(){
        show_ext(false);
    });
    $("#st-clicker-trigger").click(function(){
        show_ext(true);
    });

});


})();
