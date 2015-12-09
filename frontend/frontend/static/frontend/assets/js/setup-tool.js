(function(){

var MODE_INACTIVE = 1,
    MODE_PICKING = 2,
    MODE_PICKED = 3;

var itemsData = {
    title: { id: null, elementHoverBg: '#FFEB0D', elementSelectedBg: '#006dcc', mode: MODE_INACTIVE },
    description: { id: null, elementHoverBg: '#FFEB0D', elementSelectedBg: '#2f96b4', mode: MODE_INACTIVE }
};

function updateButtonAndData(itemData, new_mode, tag_id){
    if (new_mode)
        itemData.mode = new_mode;
    switch (itemData.mode) {
        case MODE_INACTIVE:
            $('#st-title').css('color', '#FFEB0D');
            $('#st-title').addClass('disabled');
            itemData.id = null;
            break;
        case MODE_PICKING:
            $('#st-title').css('color', '#FFEB0D');
            $('#st-title').removeClass('disabled');
            itemData.id = null;
            break;
        case MODE_PICKED:
            $('#st-title').css('color', 'white');
            itemData.id = tag_id;
            break;
    }
}


var BG_DATA_KEY = 'st-origin-background';

function setBg(element, bg) {
    if (!$(element).data(BG_DATA_KEY))
        $(element).data(BG_DATA_KEY, $(element).css('background')); // backup
    $(element).css({'background': bg});
}
function clearBg(element) {
    if ($(element).data(BG_DATA_KEY))
        $(element).css({'background': $(element).data(BG_DATA_KEY)});
}

function selectElement(element, itemData) {
    setBg(element, itemData.elementSelectedBg);
}

function unselectElement(element) {
    clearBg(element);
}

function styleHoverElement(element) {
    setBg(element, itemsData.title.elementHoverBg);
}

function unstyleHoverElement(element) {
    clearBg(element);
}

function onIframeElementClick(event) {
    event.stopPropagation();

    if (!$(this).attr('tag-id'))
        return;

    // unpick by click
    if (itemsData.title.mode == MODE_PICKED && itemsData.title.id == $(this).attr('tag-id')) {
        unselectElement($('iframe').contents().find('*[tag-id='+ itemsData.title.id +']')[0]);
        updateButtonAndData(itemsData.title, MODE_PICKING);
        styleHoverElement(this);
    }
    // pick by click
    else if (itemsData.title.mode == MODE_PICKING) {
        selectElement(this, itemsData.title);
        updateButtonAndData(itemsData.title, MODE_PICKED, $(this).attr('tag-id'));
    }
}

var previous_hover_element = [];

function onIframeElementHover(event) {
    event.stopPropagation();

    //console.log(event.type + $(this).attr('tag-id'));
    
    if (!$(this).attr('tag-id')) // tag is not from original html
        return;

    if ($(this).prop("tagName")) // is not document object
        if (itemsData.title.mode == MODE_PICKING)
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
    if (itemsData.title.mode == MODE_INACTIVE) { // start
        if (!events_ready) { // temp logic: attche events on first button click
            $('iframe').contents().on('mouseenter mouseleave', '*', onIframeElementHover);
            $('iframe').contents().on('click', '*', onIframeElementClick);
            events_ready = true;
        }
        
        updateButtonAndData(itemsData.title, MODE_PICKING);
    }
    else { // stop picking
        if (itemsData.title.mode == MODE_PICKED)
            unselectElement($('iframe').contents().find('*[tag-id='+ itemsData.title.id +']')[0]);
        updateButtonAndData(itemsData.title, MODE_INACTIVE);
    }
}

$(document).ready(function(){
    $(document).on('click', '#st-title', onItemButtonClick);
});

})();
