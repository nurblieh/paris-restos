/* ===================================================
   main.js for paris-restos.
   =================================================== */

var gMap;


function light_pins(event) {
  target_zip = event.target.id.replace('-tab', '')
  // Zoom to a view which includes all restos for this postal code.
  // Previously calculated during map init below.
  gMap.fitBounds(restos_json[target_zip].latlngBounds);
  for (var zip in restos_json) {
    // Test that the current postal code matches the current "tab".
    var new_state = (zip == target_zip);
    for (var i = 0; i < restos_json[zip].length; i++) {
      restos_json[zip][i].marker.setVisible(new_state);
    }
  }
}


function init_map() {
  google.maps.visualRefresh = true;
  var mapOptions = {
    center: new google.maps.LatLng(48.8530, 2.3498), // Paris, Ile de la Cite.
    zoom: 11,
    mapTypeId: google.maps.MapTypeId.ROADMAP
  };
  gMap = new google.maps.Map(document.getElementById("map-canvas"),
                             mapOptions);
  // Create one InfoWindow instance and re-use it for whichever marker.
  infoWindow = new google.maps.InfoWindow();
  infoWindow.currentId = null;
  for (var zip in restos_json) {
    for (var i = 0; i < restos_json[zip].length; i++) {
      lat = restos_json[zip][i].coords.lat;
      lon = restos_json[zip][i].coords.lon;
      // Create a marker for each resto. But don't make it visible.
      var coords = new google.maps.LatLng(lat, lon)
      restos_json[zip][i].marker = new google.maps.Marker({
        position: coords,
        map: gMap,
        title: restos_json[zip][i].name,
        visible: false,
      });
      // For each postal code, create a bounding box for the map viewport.
      if (typeof(restos_json[zip].latlngBounds) == 'undefined') {
        restos_json[zip].latlngBounds = new google.maps.LatLngBounds();
      }
      restos_json[zip].latlngBounds.extend(coords);
      // Listen for a click on this marker and popup our InfoWindow.
      restos_json[zip][i].marker.resto_id = restos_json[zip][i].id
      google.maps.event.addListener(restos_json[zip][i].marker, 'click', function() {
        // Un-highlight the current row in our resto table.
        if (infoWindow.currentId) {
          $('#row-' + infoWindow.currentId).removeClass('info');
        }
        infoWindow.currentId = this.resto_id
        infoWindow.setContent(this.title);
        infoWindow.open(gMap, this);
        $('#row-' + this.resto_id).addClass('info');
      });
    }
  }
  // bootstrap.js will 'activate' the navbar tabs at the top on scroll.
  $(".navbar .nav li").on("activate", function(event) {
    if (infoWindow.currentId) {
      $('#row-' + infoWindow.currentId).removeClass('info');
      infoWindow.close();
    }
    light_pins(event);
  });
}

if (typeof(google) != 'undefined') {
  google.maps.event.addDomListener(window, 'load', init_map);
}
