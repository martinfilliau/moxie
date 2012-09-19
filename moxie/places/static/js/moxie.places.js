$(document).ready(function() {
    var map = L.map('map').setView([51.75310, -1.2600], 15);

    L.tileLayer('http://{s}.tile.cloudmade.com/b0a15b443b524d1a9739e92fe9dd8459/997/256/{z}/{x}/{y}.png', {
        maxZoom: 18,
        // Detect retina - if true 4* map tiles are downloaded
        detectRetina: true
        }).addTo(map);

    map.attributionControl.setPrefix('');

    $('#places-search').submit(function(ev) {
        ev.preventDefault();
        var form = ev.currentTarget;
        $.ajax({
            data: $(form).serializeArray(),
            dataType: 'json',
            beforeSend: function(xhr, settings){
                history.pushState({'results_html': $('.results-list').html()}, 'Moxie - Search', settings.url);
            }
        }).success(function(data){
            $('.results-list').html(Handlebars.templates.results(data));
            update_map_markers();
        });
        return false;
    });

    function geo_error(error)
    {
        // TODO: How do we want to handle being unable to get user location data.
        $('#places-search').submit();
        alert("Could not access your location.");
    }
    function handle_geolocation_query(position){
        $('#places-search input[name=lat]').val(position.coords.latitude);
        $('#places-search input[name=lon]').val(position.coords.longitude);
        var you = new L.LatLng($('#places-search input[name=lat]').val(), $('#places-search input[name=lon]').val());
        $('#places-search').submit();
        L.marker(you, {'title': "You are here."}).addTo(map);
        map.panTo(you);
    }
    function initiate_geolocation() {
        // Watch the location using high accuracy. Allow results from within the last minute times out after 20secs
        var wpid = navigator.geolocation.watchPosition(handle_geolocation_query, geo_error, {enableHighAccuracy:true, maximumAge:60000, timeout:20000});
    }
    function update_map_markers(){
        $('.results-list li').each(function(index) {
            L.marker(new L.LatLng($(this).data('lat'), $(this).data('lon')),
                {'title': $(this).find('h3').text()}
                ).addTo(map);
        });
    }
    initiate_geolocation();
    update_map_markers();
    window.onpopstate = function(event) {
        if (event.state) {
            console.log(event);
            $('.results-list').html(event.state['results_html']);
        }
    }
});
