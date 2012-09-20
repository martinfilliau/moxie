$(document).ready(function() {
    var map = L.map('map').setView([51.75310, -1.2600], 15);

    L.tileLayer('http://{s}.tile.cloudmade.com/b0a15b443b524d1a9739e92fe9dd8459/997/256/{z}/{x}/{y}.png', {
        maxZoom: 18,
        // Detect retina - if true 4* map tiles are downloaded
        detectRetina: true
        }).addTo(map);

    map.attributionControl.setPrefix('');

    function run_search() {
        var query = $('#list-bar :input[name=q]').val();
        var url = query ? "?"+$.param({'q': query}) : '';
        var headers;
        if (user_position) {
            headers = {'Geo-Position': user_position.join(';')}
        }
        $.ajax({
            url: url,
            dataType: 'json',
            headers: headers,
        }).success(function(data){
            history.pushState({'results': data}, 'Moxie - Search', url);
            $('.results-list').html(Handlebars.templates.results(data));
            update_map_markers();
        });
    }

    $('#list-bar :input[name=q]').keypress(function(ev) {
        if (ev.which == 13) {
            ev.preventDefault();
            run_search();
            return false;
        }
    });

    $('#home a').click(function(ev) {
        ev.preventDefault();
        window.history.back();
        return false;
    });

    function geo_error(error)
    {
        // TODO: How do we want to handle being unable to get user location data.
        if (!user_position) {
            console.log("No user location");
        }
        run_search();
    }
    var user_position = null;
    function handle_geolocation_query(position){
        user_position = [position.coords.latitude, position.coords.longitude];
        var you = new L.LatLng(position.coords.latitude, position.coords.longitude)
        L.marker(you, {'title': "You are here."}).addTo(map);
        map.panTo(you);
        run_search();
    }
    function initiate_geolocation() {
        // Watch the location using high accuracy. Allow results from within the last minute times out after 20secs
        var wpid = navigator.geolocation.watchPosition(handle_geolocation_query, geo_error, {maximumAge:60000, timeout:20000});
    }
    var markers = [];
    var latlngs = [];
    function update_map_markers(){
        $.each(markers, function(index) {
            map.removeLayer(this);
        });
        // Empty our lists
        markers = [];
        latlngs = [];
        $('.results-list li').each(function(index) {
            var latlng = new L.LatLng($(this).data('lat'), $(this).data('lon'));
            var marker = new L.marker(latlng, {'title': $(this).find('h3').text()});
            marker.addTo(map);
            latlngs.push(latlng);
            markers.push(marker);
        });
        var bounds = new L.LatLngBounds(latlngs);
        bounds.pad(5);
        map.fitBounds(bounds);
    }
    initiate_geolocation();
    update_map_markers();
    window.onpopstate = function(event) {
        if (event.state) {
            $('.results-list').html(Handlebars.templates.results(event.state.results));
            $('#list-bar :input[name=q]').val(event.state.results.query);
            update_map_markers();
        }
    }
});
