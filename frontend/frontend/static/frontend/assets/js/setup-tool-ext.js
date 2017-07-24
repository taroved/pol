(function(){

// skip non setup page
if (!document.location.href.match('https?://[^/]+/[^/]+/setup\?.+'))
    return;

function init_tool(pathes) {
}

function check_pathes(pathes) {
}

function update_tool_ui(config) {
}

window.ext_tool = {
    'init': init_tool,
    'check': check_pathes,
    'update_ui': update_tool_ui
};

function show_ext(show) {
    $("#st-ext-trigger")[0].style.display = show ? "inline-block" : "none";
    $("#st-clicker-trigger")[0].style.display = !show ? "inline-block" : "none";
    $("#st-extended")[0].style.display = !show ? "block" : "none";
    $("#st-clicker")[0].style.display = show ? "block" : "none";
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
