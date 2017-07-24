(function(){

var angle = 0;
var speed = {x: -1.0, y: 0.0, rotation: 1.0};
var g = 10.0;
var pos = {left: 0, top: 0};

var style; //= document.getElementById('buoy').style;
var cont_el; //= document.getElementById('help');
var cont; //= cont_el.style;

function rect() {
  return cont_el.getBoundingClientRect();
}

function height(_rect) {
  return window.innerHeight - _rect.bottom;
}

var shot_msecs = 10;
var timer = 500;
function shot() {
  if (timer == 500) {
    // init
    pos.left = rect().left;
    pos.top = rect().top;
    cont.position = 'fixed';
  }

  pos.top += speed.y;
  pos.left += speed.x;

  speed.y += g * shot_msecs / 1000;

  angle += speed.rotation;
  
  style.transform = "rotate("+ angle + "deg)";
  cont.left = pos.left + "px";
  cont.top = pos.top + "px";

  if (angle < 0)
    angle += 360;
  else if (angle >= 360)
    angle -= 360;
  
  var _rect = rect();
  // collation with ground
  if (height(_rect) - speed.y < 0) {
    speed.y = - speed.y / 2;
    speed.rotation -= 1;
    speed.x -= 1;
  }

  // continue until window left border
  if (_rect.left + speed.x > -_rect.width)
     setTimeout(shot, shot_msecs);
  else {
    //restore
    cont.position = 'absolute';
    cont.left = "";
    cont.top = "0px";
    speed = {x: -1.0, y: 0.0, rotation: 1.0};
    pos = {right: 0, top: 0};
    opacity();
  }
}

var v = 0
function opacity() {
  cont.opacity = v;
  v += 0.01;
  if (v < 1)
    setTimeout(opacity, shot_msecs);
  else
    v = 0;
}


window.onYouTubeIframeAPIReady = function() { // doesn't work
  window.player = new YT.Player('helpPlayer', {
  });
};

$(document).ready(function() {
  if (!document.getElementById('buoy'))
    return;
  style = document.getElementById('buoy').style;
  cont_el = document.getElementById('help');
  cont = cont_el.style;
  
  $('#helpModalRef').click(shot);
  
  $('#helpModal').on('hidden', function() {
    if (window.player)
      window.player.stopVideo(); 
  })
});


})();
