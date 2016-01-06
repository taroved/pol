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

var styles = {
    'title_manual': new Style('#006dcc', 'white'),
    'title_calculated': new Style('#0044CC', 'white'),
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
    unstyle: function(element, style_name) {
        var id = element.attr('tag-id'),
            names = styleTool.style_names,

        // remove style from list
        names.splice(names.indexOf(style_name), 1);

        // apply previous style
        if (id in names && names[id].length)
            styles[names[id][0]].applyStyle(element);
        else
            origin_styles[id].applyStyle(element);
    },
    unstyleMarker: function(marker) {
        var element = marker.element,
            style_name = marker.style;
        styleTool.unstyle(element, style_name);
    }
};

/**
* Marker class. Combination of element, element style, and element click handler.
*/
function Marker(element, style, click_handler) {
    this.element = element;
    this.style = style;
    this.click_event = $(this.element).click(click_handler);

    var m = this;
    this.remove = function() {
        styleTool.unstyleMarker(marker);
        $(m.element).unbind(m.click_event);
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

    var that = this;
    function _button_click() {
        switch (state) {
            case STATE_INACTIVE:
                that.state = STATE_SELECTING;
                currentItem = that.name;
                break;
            case STATE_SELECTING:
                that.state = STATE_INACTIVE;
                currentItem = null;
                break;
            case STATE_SELECTED:
                //remove markers
                that.state = STATE_SELECTING;
                currentItem = null;
                break;
        }
        _update_button();
    }
    $(this.button).click(_button_click);

    function _update_button(){
        switch (state) {
            case STATE_INACTIVE:
                button.css('color', 'white');
                button.addClass('disabled');
                currentItem = null;
                break;
            case MODE_SELECTING:
                button.css('color', '#FFEB0D');
                button.removeClass('disabled');
                currentItem = null;
                break;
            case MODE_SELECTED:
                button.css('color', 'white');
                currentItem = name;
                break;
        }
    }
    
    /**
    * Invokes when current item is active
    */
    this.onSelectionElementClick = function(element) {
        that._markers = [];
        // mark current element
        that.manual_marker = new Marker(element, styles[that.name +'_manual'], that._manual_marker_click);
        that._markers.push(that.manual_marker);

        //todo: freeze UI
        requestSelection().then(function(data){
            // go by items
            for (var name in data) {
                var item = items[name],
                    manual_id = item.manual_marker.element.attr('tag-id');

                    // remove all markers except manual marker
                    item._markers = [item.manual_marker];
                // go by tag-ids for item
                for (var id in items[name]) {
                    if (id != manual_id)
                        item._markers.push(new Marker(id2el[id], styles[item.name +'_calculated'], function(){}));
                }
            }
        }, function(error){
            //todo: unfreez UI
            console.log('Server error: '+ error);
        });
    }

    this._manual_marker_click = function() {
        //remove markers
        that._markers.forEach(function(marker){
            marker.remove();
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

// generate json [tag_name, {attributes_dict}, [children]]

var iframeHtmlJson = null;

function buildJsonFromHtml(doc) {
    function tag2json(tag) {
        if (tag.attr('tag-id')) {
            var tagJson = [tag.prop("tagName").toLowerCase(), {'tag-id': tag.attr('tag-id')}],
                children = [];
            tag.children().each(function(_, t){
                var res = tag2json($(t));
                Array.prototype.push.apply(children, res);
            });
            tagJson.push(children);
            return [ tagJson ]
        }
        else {
            var tagListJson = [];
            tag.children().each(function(_, t){
                var res = tag2json($(t));
                Array.prototype.push.apply(tagListJson, res);
            });
            return tagListJson;
        }
    }

    if (!iframeHtmlJson)
        iframeHtmlJson = tag2json(doc.find(':root'))[0];
    return iframeHtmlJson;
}

function requestSelection() {
    var htmlJson = buildJsonFromHtml($('iframe').contents());

    var name_ids = {};
    for (var name in items) {
        if (items[name].state == STATE_SELECTED)
            name_ids[name] = $(items[name].manual_marker.element).attr('tag-id');
    }

    var promise = {
        _success: function(data) { console.log('Undefined success handler'); },
        _fail: function(error) { console.log('Undefined fail handler'); },
        then: function(success, fail) {
            promise._success = success;
            promise._fail = fail;
        }
    };

    $.ajax({
        type: 'POST',
        url: "/setup_get_selected_ids",
        data: JSON.stringify({ html: htmlJson, names: name_ids }),
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        headers: {"X-CSRFToken": getCookie('csrftoken')},
        success: function(data){
            promise._success(data)
            calculatedSelection.selectIds(data);
        },
        failure: function(errMsg) {
            promise._fail(errMsg);
        }
    });
    console.log(JSON.stringify(htmlJson));
    return promise;
}
////
// --- calculation of all selections on server side
////


function onIframeElementClick(event) {
    event.stopPropagation();

    if (!curItemData)
        return;

    if (!$(this).attr('tag-id'))
        return;

    if (currentItem)
        items[currentItem].onSelectionElementClick(this);
}

var previous_hover_element = [];

function onIframeElementHover(event) {
    event.stopPropagation();

    if (!curItemData)
        return;

    if (!$(this).attr('tag-id')) // tag is not from original html
        return;

    if ($(this).prop("tagName")) // is not document object
        if (curItemData.mode == MODE_SELECTING)
            if (event.type == 'mouseenter') {
                styleHoverElement(this);
                if (this != previous_hover_element)
                    unstyleHoverElement(previous_hover_element);
                previous_hover_element = this;
            }
            else { // mouseleave
                unstyleHoverElement(this);
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

$(document).ready(function(){
    items['title'] = new Item('title', $('#st-title')[0]);
    items['description'] = new Item('description', $('#st-description')[0]);
    

    // init id2el
    $('iframe').contents().find('*[tag-id]').each(function(){
        id2el[$(this).attr('tag-id')] = this;
    });

    blinkButton($('#st-title'), 3);
    $('#st-title').tooltip('show');
});


})();
