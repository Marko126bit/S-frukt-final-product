// Static Background Script
// This script adds a canvas with a linear gradient that transitions from black to blue at the top and then smoothly to black again.

document.addEventListener("DOMContentLoaded", function() {
  var canvas = document.createElement('canvas');
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
  canvas.style.position = "absolute";
  canvas.style.top = 0;
  canvas.style.left = 0;
  canvas.style.zIndex = -1;
  document.body.insertBefore(canvas, document.body.firstChild);

  var ctx = canvas.getContext('2d');

  function updateCanvas() {
    var gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
    gradient.addColorStop(0, 'black'); // Black at the top
    gradient.addColorStop(0.4, '#003366'); // Blue towards the top, adjusted position
    gradient.addColorStop(0.6, '#003366'); // Blue towards the bottom, adjusted position
    gradient.addColorStop(1, 'black'); // Black at the bottom

    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
  }

  updateCanvas();

  window.addEventListener('resize', function() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    updateCanvas();
  });
});






















