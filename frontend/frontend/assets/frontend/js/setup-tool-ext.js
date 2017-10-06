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
var _validated = false;

function updateSelector(name, messages) {
    var control_group = $('#ste-'+ name).parent().parent();
    var help_text = control_group.find('.help-inline');

    if ('error' in messages) {
        control_group.removeClass('info').addClass('error');
        help_text.text(messages['error']);
    }
    else if ('count' in messages || $('#ste-'+ name).val().trim()) {
        if (!('count' in messages))
            messages['count'] = 0;
        control_group.removeClass('error').addClass('info');
        help_text.text(help_text.attr('count-tpl').replace('%s', messages['count']));
    }
    else {
        control_group.removeClass('error').removeClass('info');
        help_text.text('');
    }
}

// show status and error messages
function updateUIMessages(data) {
    updateSelector('parent', data[0]);
    ['title', 'description', 'link'].forEach(function(name){
        if (name in data[1])
            updateSelector(name, data[1][name]);
        else
            updateSelector(name, {});
    });

    hide_check_show_create(true);
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
        $('#ste-parent').val().trim(),
        {}
    ];
    ['title', 'description', 'link'].forEach(function(name){
        var xpath = $('#ste-'+ name).val();
        if (xpath.trim().length > 0)
            cfg[1][name] = xpath;
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

function showPosts(posts) {
    $('.ext-result:not(:first)').remove(); // clear results
    $post_tpl = $('.ext-result:first');
    posts.forEach(function(post){
        var i = 0;
        var $post = $post_tpl.clone();
        var $post_fields = $post.find('dl > dd > pre');
        var $post_dts = $post.find('dl > dt');
        var $post_dds = $post.find('dl > dd');
        
        ['title', 'link', 'description'].forEach(function(name){
            if (name in post) {
                $($post_fields[i]).text(post[name].trim());
                $($post_fields[i]).addClass('prettyprint');
            }
            else {
                $($post_dts[i]).remove();
                $($post_dds[i]).remove();
            }
            i++;
        });
        $post.appendTo($post_tpl.parent());
        $post[0].style.display = null; // show
    });
    PR.prettyPrint();
    $('#ext-results')[0].style.display = 'block';
    $('#ext-results .no-data')[0].style.display = posts.length == 0 ? 'block' : 'none';
    expandPosts(true);
}

function expandPosts(show) {
    $('#ext-results').collapse(show ? 'show' : 'hide');
}

function active() {
    return _active;
}
function validate() {
    return _validate;
}

window.ET = {
    'showIcon': showIcon,
    'init': init_tool,
    'check': check_pathes,
    'updateUI': updateUI,
    'updateUIMessages': updateUIMessages,
    'getUIConfig': getUIConfig,
    'active': active,
    'validate': validate
};

function show_ext(show) {
    $("#st-ext-trigger")[0].style.display = !show ? "inline-block" : "none";
    $("#st-clicker-trigger")[0].style.display = show ? "inline-block" : "none";
    $("#st-extended")[0].style.display = show ? "block" : "none";
    $("#st-clicker")[0].style.display = !show ? "block" : "none";

    if (!show)
        $('#ext-results')[0].style.display = 'none';
    
    _active = show;
}

function hide_check_show_create(hide) {
    $("#check")[0].style.display = !hide ? 'inline-block' : 'none';
    $("#create")[0].style.display = hide ? 'inline-block' : 'none';
}

function validateSelectors() {
    if (true) {
        var selectors = getUIConfig();
        return new Promise(function(resolve, reject){
            $.ajax({
                type: 'POST',
                url: "/setup_validate_selectors",
                data: JSON.stringify({ selectors: selectors, snapshot_time: snapshot_time, url:$('#create').data('page-url') }),
                contentType: "application/json; charset=utf-8",
                dataType: "json",
                headers: {"X-CSRFToken": getCookie('csrftoken')},
                success: function(data){
                    resolve(data)
                },
                failure: function(errMsg) {
                    reject(errMsg);
                }
            });
        });
    }
    else {
        return new Promise(function(resolve, reject){
            setTimeout(function(){ resolve({}); }, 0);
        });
    }
}

$(document).ready(function(){
    $("#st-ext-trigger").click(function(){
        show_ext(true);
        hide_check_show_create(false);
        return true;
    });
    $("#st-clicker-trigger").click(function(){
        var ch = changed();
        if (!ch || confirm($("#st-clicker-trigger").attr('confirm-text'))) { // show visual constructor
            show_ext(false);
            updateUI(_config);
            update_iframe_heignt();
            hide_check_show_create(true);
        }
        return true;
    });

    $("input[id^='ste-']").keyup(function(){
        hide_check_show_create(false)
    });
    $("#check").click(function(){
        loader(true);
        validateSelectors().then(function(res){
            ET.updateUIMessages(res.messages);
            showPosts(res.posts);
            hide_check_show_create(res.success);
            //unfreez UI
            loader(false);
        }, function(errMsg){
            console.error(errMsg);
            //unfreez UI
            loader(false);
        });
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
