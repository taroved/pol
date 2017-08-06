(function(){

/**
* Hash for geting element by tag-id
*/
var id2el = {};

/**
* Style class
*/
function Style(background, color) {
    this.background = background;
    this.color = color;
    this.applyStyle = function(element) {
        $(element).css({'background': background, 'color': color});
    }
}
Style.take = function(element) {
   return new Style($(element).css('background'), $(element).css('color'));
}

var styles = {
    'title_manual': new Style('#006dcc', 'white'),
    'title_calculated': new Style('#78A4F9', 'white'),
    'description_manual': new Style('#2f96b4', 'white'),
    'description_calculated': new Style('#5bc0de', 'white'),
    // selection hove style
    'hover': new Style('#FFEB0D', 'black')
};

/**
* Store styles of elements to restore them when required
*/
var styleTool = {
    // origin styles for every element
    origin_styles: {},
    // list of style for every element
    style_names: {},
   
    hasStyle: function(element, style_name) {
        var id = $(element).attr('tag-id');
        return id in styleTool.style_names
            && styleTool.style_names[id].indexOf(style_name) > -1;
    },
    unstyle: function(element, style_name) {
        var id = $(element).attr('tag-id'),
            names = styleTool.style_names[id];

        // remove style from list
        names.splice(names.indexOf(style_name), 1);

        // apply previous style
        if (names.length) {
            var last_style_name = names[names.length-1];
            styles[last_style_name].applyStyle(element);
        }
        else
            styleTool.origin_styles[id].applyStyle(element);
    },
    unstyleAll: function(style_name) {
        // clear all styles with the style_name
        for (var id in styleTool.style_names) {
            var element = id2el[id];
            while (styleTool.hasStyle(element, style_name))
                styleTool.unstyle(element, style_name);
        }
    },
    style: function(element, style_name) {
        var id = $(element).attr('tag-id');

        // add style to list
        if (!(id in styleTool.style_names))
            styleTool.style_names[id] = [];
        styleTool.style_names[id].push(style_name);
        // backup origin style
        if (!(id in styleTool.origin_styles))
            styleTool.origin_styles[id] = Style.take(id2el[id]);

        // apply style
        styles[style_name].applyStyle(element);
    },
    unstyleMarker: function(marker) {
        var element = marker.element,
            style_name = marker.style_name;
        styleTool.unstyle(element, style_name);
    },
    styleMarker: function(marker) {
        var element = marker.element,
            style_name = marker.style_name;
        styleTool.style(element, style_name);
    }
};

/**
* Marker class. Combination of element, element style, and element click handler.
*/
function Marker(element, style_name) {
    this.element = element;
    this.style_name = style_name;

    styleTool.styleMarker(this);

    var m = this;
    this.remove = function() {
        styleTool.unstyleMarker(m);
    }
}

/**
* Item states
*/
var STATE_INACTIVE = 1,
    STATE_SELECTING = 2,
    STATE_SELECTED = 3;

var currentItem = null;
/**
* Item class. Describe all logic related to separate item
*/
function Item(name, button) {

    this.name = name;
    this.button = button;
    this.manual_marker = null;
    this._markers = null;
    this.state = STATE_INACTIVE;

    var that = this;
    function _button_click() {
        switch (that.state) {
            case STATE_INACTIVE:
                that.state = STATE_SELECTING;
                if (currentItem && currentItem.state == STATE_SELECTING) {
                    currentItem.state = STATE_INACTIVE;
                    currentItem.updateButton();
                }
                currentItem = that;
                break;
            case STATE_SELECTING:
                that.state = STATE_INACTIVE;
                currentItem = null;
                break;
            case STATE_SELECTED:
                //remove markers
                that._markers.forEach(function(m){
                    m.remove();
                });
                that._markers = [];

                that.state = STATE_INACTIVE;
                currentItem = null;
                updateSelection();
                break;
        }
        that.updateButton();
        updateCreateButtonAndExtIcon();
    }
    $(this.button).click(_button_click);

    this.updateButton = function() {
        switch (that.state) {
            case STATE_INACTIVE:
                $(button).css('color', '#333');
                $(button).removeClass(that.name == 'title' ? 'btn-primary' : 'btn-info');
                break;
            case STATE_SELECTING:
                $(button).css('color', '#FFEB0D');
                $(button).addClass(that.name == 'title' ? 'btn-primary' : 'btn-info');
                break;
            case STATE_SELECTED:
                $(button).css('color', 'white');
                break;
        }
    }
    
    /**
    * Invokes when current item is active
    */
    this.onSelectionElementClick = function(element) {
        that._markers = [];
        // mark current element
        that.manual_marker = new Marker(element, that.name +'_manual');
        that._markers.push(that.manual_marker);

        updateSelection().then(function(){
            that.state = STATE_SELECTED;
            that.updateButton();
            updateCreateButtonAndExtIcon();
            currentItem = null;
        });
    }

    function updateSelection() {
        //todo: freeze UI
        loader(true);
        return requestSelection().then(function(data){
            if (!('xpathes' in data && 'ids' in data)) // removed all selections
                data = [[] ['', []]];

            // go by items
            for (var name in data.ids) {
                var item = items[name],
                    manual_id = $(item.manual_marker.element).attr('tag-id');

                // remove all markers except manual marker
                item._markers = item._markers.filter(function(m){
                    var remove = m != item.manual_marker;
                    if (remove)
                        m.remove(); // remove handlers and style
                    return !remove;
                });
                // go by tag-ids for item
                data.ids[name].forEach(function(id){
                    if (id != manual_id)
                        item._markers.push(new Marker(id2el[id], item.name +'_calculated'));
                });
                // remove all hover styles
                styleTool.unstyleAll('hover');
            }

            // update extended tool selectors
            xpathes = 'xpathes' in data ? data.xpathes : ['', []];
            ET.updateUI(xpathes);

            loader(false);
            return {};
        }, function(error){
            //unfreez UI
            loader(false);
            alert("Server error. Developer note: check console log")
            console.log('Server error: '+ error);
        });
    }
}

var items = {};

function blinkButton(element, times) {
    times *= 2;
    var show = true;
    function toggle() {
        element.tooltip(show ? 'show' : 'hide');
        times --;
        show = !show;
        if (times)
            setTimeout(toggle, 1000);
    }
    toggle();
}

////
// +++ calculation of all selections on server side
////

// used only for getting of csrftoken and putting it into request header; I'm not sure if it's required
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

window.getCookie = getCookie;

// html2json [tag_name, {attributes_dict}, [children]]
var iframeHtmlJson = null;

function gatherSelectedTagIds(name_ids) {
    var selected_any = false;
    for (var name in items) {
        if ([STATE_SELECTING, STATE_SELECTED].indexOf(items[name].state) != -1) {
            name_ids[name] = $(items[name].manual_marker.element).attr('tag-id');
            selected_any = true;
        }
    }
    return selected_any;
} 

function requestSelection() {
    // gather selected tag-ids
    var name_ids = {};
    selected_any = gatherSelectedTagIds(name_ids);

    if (selected_any)
        return new Promise(function(resolve, reject){
            $.ajax({
                type: 'POST',
                url: "/setup_get_selected_ids",
                data: JSON.stringify({ html: iframeHtmlJson, names: name_ids }),
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
    else {
        return new Promise(function(resolve, reject){
            setTimeout(function(){ resolve({}); }, 0);
        });
    }
}
////
// --- calculation of all selections on server side
////


function onIframeElementClick(event) {
    event.stopPropagation();

    if (currentItem)
        currentItem.onSelectionElementClick(this);
}

function onIframeElementHover(event, p1, p2, p3) {
    
    if (!currentItem)
        return;

    if ($(this).prop("tagName")) // is not document object
        if (currentItem.state == STATE_SELECTING)
            if (event.type == 'mouseenter' && $(this).attr("tag-id")) {
                // clear all hover styles
                styleTool.unstyleAll('hover');
                styleTool.style(this, 'hover');
                event.stopPropagation()
            }
            else { // mouseleave
                styleTool.unstyle(this, 'hover');
                // style parent document element
                var element = this;
                while (element) {
                    element = element.parentNode;
                    if ($(element).attr("tag-id")) {
                        styleTool.style(element, 'hover');
                        break;
                    }
                }
            }
}

var events_ready = false;

function onItemButtonClick(event) {
    var item_name = $(this).attr('id').substring('st-'.length);

    if (curItemData && curItemData != itemsData[item_name]) {
        // disable another button if it was active
        if (curItemData.mode == MODE_SELECTING)
            updateButtonAndData(curItemData, MODE_INACTIVE);
    }

    curItemData = itemsData[item_name];

    if (curItemData.mode == MODE_INACTIVE) { // start
        if (!events_ready) { // temp logic: attche events on first button click
            $('iframe').contents().on('mouseenter mouseleave', '*', onIframeElementHover);
            $('iframe').contents().on('click', '*', onIframeElementClick);
            events_ready = true;
        }
        
        updateButtonAndData(curItemData, MODE_SELECTING);
    }
    else { // stop picking
        if (curItemData.mode == MODE_SELECTED)
            unselectElement($('iframe').contents().find('*[tag-id='+ curItemData.id +']')[0]);
        updateButtonAndData(curItemData, MODE_INACTIVE);
        calculatedSelection.unselectItem(curItemData.name);

        curItemData = null;
    }
}
////
// ++++ Create button logic
////
function updateCreateButtonAndExtIcon() {
    var selected = false;

    for (var name in items)
        if (items[name].state == STATE_SELECTED) {
            selected = true;
            break;
        }

    if (selected)
        $('#create').removeClass('disabled');
    else
        $('#create').addClass('disabled');
    
    ET.showIcon(selected && (!currentItem || currentItem.state != STATE_SELECTING)); // hide ext icon in time of selection
}

function onCreateButtonClick() {
    var active = !$('#create').hasClass('disabled');
    if (active) {
        //freeze UI
        loader(true);
        createFeed().then(function(data){
            if (ET.active()) {
                var res = JSON.parse(data);
                if (res.success)
                    window.location.href = res.url; // feed_page_url
                else {
                    ET.updateUIMessages(res.messages);
                    //unfreez UI
                    loader(false);
                }
            }
			else
				window.location.href = data; // feed_page_url
        }, function(error){
            console.log('Server error: '+ error);
            //unfreez UI
            loader(false);
        });
    }
}

function createFeed() {
    var selectors = null;
    if (ET.active()) {
        selectors = ET.getUIConfig();
    }
    else {
        // gather selected tag-ids
        var name_ids = {};
        selected_any = gatherSelectedTagIds(name_ids);
    }

    if (selected_any)
        return new Promise(function(resolve, reject){
            $.ajax({
                type: 'POST',
                url: ET.active() ? "/setup_create_feed_ext" :"/setup_create_feed",
                data: JSON.stringify(ET.active()
                                     ? { selectors: selectors, snapshot_time: snapshot_time, url:$('#create').data('page-url') }
                                     : { html: iframeHtmlJson, names: name_ids, url:$('#create').data('page-url') }
                                    ),
                contentType: "application/json; charset=utf-8",
                headers: {"X-CSRFToken": getCookie('csrftoken')},
                success: function(data){
                    resolve(data)
                },
                failure: function(errMsg) {
                    reject(errMsg);
                }
            });
        });
    else {
        return new Promise(function(resolve, reject){
            setTimeout(function(){ resolve({}); }, 0);
        });
    }
}
////
// ++++ Create button logic
////

// Spinner
function loader(show) {
  document.getElementById("loader-bg").style.display = show ? "block" : "none";
}
window.loader = loader;

$(document).ready(function(){
    // skip non setup page
    if (!document.location.href.match('https?://[^/]+/[^/]+/setup\?.+'))
        return;

    loader(true);
    
    items['title'] = new Item('title', $('#st-title')[0]);
    items['description'] = new Item('description', $('#st-description')[0]);
   
    $('#create').click(onCreateButtonClick);
 
    $('iframe').load(function(){
        // init id2el
        $('iframe').contents().find('*[tag-id]').each(function(){
            id2el[$(this).attr('tag-id')] = this;
        });
        // attach iframe elements event handlers
        $('iframe').contents().on('click', '*[tag-id]', onIframeElementClick);
        $('iframe').contents().on('mouseenter mouseleave', '*[tag-id]', onIframeElementHover);
		var iframe_window = $('iframe')[0].contentWindow;
        iframeHtmlJson = iframe_window.html2json;
		snapshot_time = iframe_window.snapshot_time;
        loader(false);
    });

    $('#st-title').tooltip('show');
});


})();
