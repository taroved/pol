(function(){

var MODE_INACTIVE = 1,
    MODE_PICKING = 2,
    MODE_PICKED = 3;

var itemsData = {
    title: { id: null, elementHoverBg: '#FFEB0D', elementSelectedBg: '#006dcc', mode: MODE_INACTIVE, name: 'title' },
    description: { id: null, elementHoverBg: '#FFEB0D', elementSelectedBg: '#2f96b4', mode: MODE_INACTIVE, name: 'description' }
};

var curItemData = null;

////
// +++ calculation of all selections on server side
////

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

function calcAllSelections() {
    var htmlJson = buildJsonFromHtml($('iframe').contents());

    var name_ids = {};
    for (var name in itemsData) {
        if (!!itemsData[name].id)
            name_ids[name] = itemsData[name].id;
    }

    $.ajax({
        type: 'POST',
        url: "/setup_generate_selected_ids",
        data: JSON.stringify({ html: htmlJson, names: name_ids }),
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        headers: {"X-CSRFToken": getCookie('csrftoken')},
        success: function(data){console.log(data);},
        failure: function(errMsg) {
            console.log('Error:'+ errMsg);
        }
    });
    console.log(JSON.stringify(htmlJson));
}
////
// --- calculation of all selections on server side
////


function updateButtonAndData(itemData, new_mode, tag_id){
    if (new_mode)
        itemData.mode = new_mode;
    var button = $('#st-'+ itemData.name);
    switch (itemData.mode) {
        case MODE_INACTIVE:
            button.css('color', 'white');
            button.addClass('disabled');
            itemData.id = null;
            break;
        case MODE_PICKING:
            button.css('color', '#FFEB0D');
            button.removeClass('disabled');
            itemData.id = null;
            break;
        case MODE_PICKED:
            button.css('color', 'white');
            itemData.id = tag_id;
            break;
    }
}


var BG_DATA_KEY = 'st-origin-background';
var PICKED_NAMES_KEY = 'st-picked-item-names';

function setBg(element, bg, pick) {
    // save origin background if it's not saved
    if (typeof($(element).data(BG_DATA_KEY)) == 'undefined')
        $(element).data(BG_DATA_KEY, $(element).css('background'));
    // if it's picked element we push the item id into array
    if (pick) { // redo for multiselect
        if (typeof($(element).data(PICKED_NAMES_KEY)) == 'undefined')
            $(element).data(PICKED_NAMES_KEY, []);
        $(element).data(PICKED_NAMES_KEY).push(curItemData.name);
    }

    $(element).css({'background': bg});
}
function clearBg(element, unpick) {
    if (unpick) { // redo for multiselect
        var picked_names = $(element).data(PICKED_NAMES_KEY);
        // remove current item id from element
        if (picked_names.indexOf(curItemData.name) > -1)
            picked_names.splice(picked_names.indexOf(curItemData.name), 1);
    }

    // for first take selection color if element was selected
    var picked_names = $(element).data(PICKED_NAMES_KEY);
    if (typeof(picked_names) != 'undefined' && picked_names.length) {
        var name = picked_names[picked_names.length-1];
        $(element).css({'background': itemsData[name].elementSelectedBg});
    }
    // get original background if it saved
    else if (typeof($(element).data(BG_DATA_KEY)) != 'undefined')
        $(element).css({'background': $(element).data(BG_DATA_KEY)});
}

function selectElement(element, itemData) {
    setBg(element, itemData.elementSelectedBg, true);
}

function unselectElement(element) {
    clearBg(element, true);
}

function styleHoverElement(element) {
    setBg(element, curItemData.elementHoverBg);
}

function unstyleHoverElement(element) {
    clearBg(element);
}

function onIframeElementClick(event) {
    event.stopPropagation();

    if (!curItemData)
        return;

    if (!$(this).attr('tag-id'))
        return;

    // unpick by click
    if (curItemData.mode == MODE_PICKED && curItemData.id == $(this).attr('tag-id')) {
        unselectElement($('iframe').contents().find('*[tag-id='+ curItemData.id +']')[0]);
        updateButtonAndData(curItemData, MODE_PICKING);
        styleHoverElement(this);
    }
    // pick by click
    else if (curItemData.mode == MODE_PICKING) {
        selectElement(this, curItemData);
        updateButtonAndData(curItemData, MODE_PICKED, $(this).attr('tag-id'));
        calcAllSelections();
    }
}

var previous_hover_element = [];

function onIframeElementHover(event) {
    event.stopPropagation();

    if (!curItemData)
        return;

    if (!$(this).attr('tag-id')) // tag is not from original html
        return;

    if ($(this).prop("tagName")) // is not document object
        if (curItemData.mode == MODE_PICKING)
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
        if (curItemData.mode == MODE_PICKING)
            updateButtonAndData(curItemData, MODE_INACTIVE);
    }

    curItemData = itemsData[item_name];

    if (curItemData.mode == MODE_INACTIVE) { // start
        if (!events_ready) { // temp logic: attche events on first button click
            $('iframe').contents().on('mouseenter mouseleave', '*', onIframeElementHover);
            $('iframe').contents().on('click', '*', onIframeElementClick);
            events_ready = true;
        }
        
        updateButtonAndData(curItemData, MODE_PICKING);
    }
    else { // stop picking
        if (curItemData.mode == MODE_PICKED)
            unselectElement($('iframe').contents().find('*[tag-id='+ curItemData.id +']')[0]);
        updateButtonAndData(curItemData, MODE_INACTIVE);

        curItemData = null;
    }
}

$(document).ready(function(){
    $(document).on('click', '*[id^="st-"]', onItemButtonClick);
});

})();
