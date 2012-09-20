$(document).ready(function() {
    var map = L.map('map').setView([51.75310, -1.2600], 15);

    L.tileLayer('http://{s}.tile.cloudmade.com/b0a15b443b524d1a9739e92fe9dd8459/997/256/{z}/{x}/{y}.png', {
        maxZoom: 18,
        // Detect retina - if true 4* map tiles are downloaded
        detectRetina: true
        }).addTo(map);

    map.attributionControl.setPrefix('');

    function run_search() {
        var form = $('#places-search');
        var query = form.find(':input[name=q]').val();
        var url = query ? "?"+$.param({'q': query}) : '';
        $.ajax({
            url: url,
            dataType: 'json',
        }).success(function(data){
            history.pushState({'results': data}, 'Moxie - Search', url);
            $('.results-list').html(Handlebars.templates.results(data));
            update_map_markers();
        });
    }

    $('#places-search input[name=q]').keypress(function(ev) {
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
        alert("Could not access your location.");
        run_search();
    }
    function handle_geolocation_query(position){
        $('#places-search input[name=lat]').val(position.coords.latitude);
        $('#places-search input[name=lon]').val(position.coords.longitude);
        run_search();
        var you = new L.LatLng($('#places-search input[name=lat]').val(), $('#places-search input[name=lon]').val());
        L.marker(you, {'title': "You are here."}).addTo(map);
        map.panTo(you);
    }
    function initiate_geolocation() {
        // Watch the location using high accuracy. Allow results from within the last minute times out after 20secs
        var wpid = navigator.geolocation.watchPosition(handle_geolocation_query, geo_error, {enableHighAccuracy:true, maximumAge:60000, timeout:20000});
    }
    var markers = [];
    function update_map_markers(){
        $.each(markers, function(index) {
            map.removeLayer(this);
        });
        $('.results-list li').each(function(index) {
            var marker = L.marker(new L.LatLng($(this).data('lat'), $(this).data('lon')), {'title': $(this).find('h3').text()});
            marker.addTo(map);
            markers.push(marker);
        });
    }
    initiate_geolocation();
    update_map_markers();
    window.onpopstate = function(event) {
        if (event.state) {
            $('.results-list').html(Handlebars.templates.results(event.state.results));
            $('#places-search input[name=q]').val(event.state.results.query);
            update_map_markers();
        }
    }

    Handlebars.registerHelper('openingHours', function(string) {
        if(string === "") {
            return ""
        }
        result = TimeDomain.evaluateInTime(string);
        if(result.value === true) {
            return " (open)";
        } else {
            return " (closed)";
        }
    });
});
