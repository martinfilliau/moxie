var map = L.map('map').setView([51.75310, -1.2600], 15);

L.tileLayer('http://{s}.tile.cloudmade.com/b0a15b443b524d1a9739e92fe9dd8459/997/256/{z}/{x}/{y}.png', {
    maxZoom: 18,
    // Detect retina - if true 4* map tiles are downloaded
    detectRetina: true
}).addTo(map);

map.attributionControl.setPrefix('');