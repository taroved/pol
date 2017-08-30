(function(){

// skip non setup page
if (!document.location.href.match('https?://[^/]+/[^/]+/setup\?.+'))
    return;

$(document).ready(function(){
	var editor = ace.edit("ste-parent");
	editor.setTheme("ace/theme/sqlserver");
	editor.session.setMode("ace/mode/xquery");
});


})();