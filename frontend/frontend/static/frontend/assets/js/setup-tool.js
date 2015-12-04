(function(){

var BG_DATA_KEY = 'st-origin-background';

function styleHoverElement(element) {
    $(element).data(BG_DATA_KEY, $(element).css('background'));
    $(element).css({'background': 'yellow'});
}

function unstyleHoverElement(element) {
    $(element).css({'background': $(element).data(BG_DATA_KEY)});
}

var previous_hover_element = null;

function onIframeElementHover(event) {
    event.stopPropagation();

    if ($(this).prop("tagName")) // is not document object
        if (event.type == 'mouseenter') {
            styleHoverElement(this);
            if (previous_hover_element)
                unstyleHoverElement(previous_hover_element);
            previous_hover_element = this;
        }
        else {
            unstyleHoverElement(this);
        }
}

function onItemButtonClick(event) {
    if ($(this).hasClass('disabled')) { // start picking
        $(this).removeClass('disabled');
        $('iframe').contents().on('mouseenter mouseleave', '*', onIframeElementHover);
    }
    else { // stop picking
        $(this).addClass('disabled');
        $('iframe').contents().off('mouseenter mouseleave', '*', onIframeElementHover);
    }
}

$(document).ready(function(){
    $(document).on('click', '#st-title', onItemButtonClick);
});

})();
