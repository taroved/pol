(function(){

// skip non setup page
if (!document.location.href.match('https?://[^/]+/[^/]+/setup\?.+'))
    return;

function save(key, obj) {
    if (typeof(localStorage) !== "undefined") {
        var tm = new Date().getTime();
        var v = {time: tm, value: obj}
        localStorage.setItem(key, JSON.stringify(v));
    }
}
function read(key) {
    var day = 24 * 60 * 60 * 1000;

    if (typeof(localStorage) !== "undefined") {
        var v = localStorage.getItem(key);
        if (v) {
            var tm = new Date().getTime();
            var v = JSON.parse(v);
            if (tm - v.time < day) {
                return v.value;
            }
        }
    }
}

window.save = save;
window.read = read;

function init_tool(pathes) {
}

function check_pathes(pathes) {
}

var _config = ['', {}];
var _active = false;

function updateSelector(name, messages) {
    var control_group = $('#ste-'+ name).parent().parent();
    if ('error' in messages) {
        control_group.removeClass('info').addClass('error');
        control_group.find('.help-inline').text(messages['error']);
    }
    else {
        control_group.removeClass('error').addClass('info');
        control_group.find('.help-inline').text(messages['count']);
    }
}

// show status and error messages
function updateUIMessages(data) {
        
}

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

function getUIConfig() {
    var cfg = [
        $('#ste-parent').val(),
        {}
    ];
    ['title', 'description', 'link'].forEach(function(name){
        cfg[1][name] = $('#ste-'+ name).val();
    });
    return cfg;
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
    'getUIConfig': getUIConfig,
    'active': active
};

function show_ext(show) {
    $("#st-ext-trigger")[0].style.display = !show ? "inline-block" : "none";
    $("#st-clicker-trigger")[0].style.display = show ? "inline-block" : "none";
    $("#st-extended")[0].style.display = show ? "block" : "none";
    $("#st-clicker")[0].style.display = !show ? "block" : "none";
    
    _active = show;
}

$(document).ready(function(){
    $("#st-ext-trigger").click(function(){
        show_ext(true);
        return true;
    });
    $("#st-clicker-trigger").click(function(){
        var ch = changed();
        if (!ch || confirm($("#st-clicker-trigger").attr('confirm-text'))) {
            show_ext(false);
            updateUI(_config);
        }
        return true;
    });

    /*var cfg = read('xpathes')
    if (cfg) {
        updateUI(cfg);
        show_ext(true);
        $("#restored-alert")[0].style.display = 'block';
    }*/
    
    /*$("#ste-parent, #ste-title, #ste-description, #ste-link").change(function(){
        save('xpathes', getUIConfig());
        return true;
    });*/
});


})();
