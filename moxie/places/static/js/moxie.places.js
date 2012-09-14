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
                history.pushState(null, 'Moxie - Search', settings.url);
            }
        }).success(function(data){
            $('.results-list').html(Handlebars.templates.results(data));
            update_map_markers();
        });
        return false;
    });

    function initiate_geolocation() {
        navigator.geolocation.getCurrentPosition(handle_geolocation_query);
    }
    function handle_geolocation_query(position){
        $('#places-search input[name=lat]').val(position.coords.latitude);
        $('#places-search input[name=lon]').val(position.coords.longitude);
        var you = new L.LatLng($('#places-search input[name=lat]').val(), $('#places-search input[name=lon]').val());
        L.marker(you, {'title': "You are here."}).addTo(map);
        map.panTo(you);
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
});