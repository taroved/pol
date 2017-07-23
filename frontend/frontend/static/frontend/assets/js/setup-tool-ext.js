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

$(document).ready(function(){


});


})();
