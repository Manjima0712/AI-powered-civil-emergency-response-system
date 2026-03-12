// Mapbox access token will be set globally or handled via environment
// mapboxgl.accessToken = "SCRUBBED" 

const suggestedDestinations = [ 
  { 
      name: "Venjaramoodu, Kerala", 
      coordinates: [76.909569, 8.682756], 
      description: "A scenic town in Kerala known for its lush greenery and traditional culture." 
  },
  { 
      name: "Sree Gokulam Medical College, Venjaramoodu", 
      coordinates: [76.9685, 8.7481], 
      description: "A renowned medical institution offering quality education and healthcare services in Kerala." 
  },
  { 
      name: "Government Higher Secondary School, Venjaramoodu", 
      coordinates: [76.9160, 8.6990], 
      description: "A government higher secondary school located at S H 47, Venjaramoodu, Thiruvananthapuram - 695607." 
  },
  { 
      name: "Government Hospital, Vamanapuram", 
      coordinates: [76.9025, 8.7200], 
      description: "A government hospital located on Hospital Road, Vamanapuram, about 3.79 km from Venjaramoodu." 
  },
  { 
      name: "Community Health Centre, Kanyakulangara", 
      coordinates: [76.8817, 8.7505], 
      description: "A community health centre located on SH-1, Kanyakulangara, about 6.56 km from Venjaramoodu." 
  },
  { 
      name: "Community Health Centre, Kallara", 
      coordinates: [76.8350, 8.6867], 
      description: "A community health centre located at Kallara Govt Hospital, Kallara, about 7.49 km from Venjaramoodu." 
  }
];

let userLocation;
let map;
let directions;
let userMarker;
let watchId;
let selectedDestinationIndex = -1;

function initMap() {
  if ("geolocation" in navigator) {
    navigator.geolocation.getCurrentPosition(successLocation, errorLocation, {
      enableHighAccuracy: true,
      timeout: 10000,
      maximumAge: 0
    });
  } else {
    errorLocation();
  }
}

function successLocation(position) {
  userLocation = [position.coords.longitude, position.coords.latitude];
  setupMap(userLocation);
  startLocationTracking();
  createDestinationSuggestions();
}

function errorLocation(error) {
  console.warn(`Geolocation error: ${error ? error.message : 'Unknown error'}`);
  // Fallback to a central location if geolocation fails - using Venjaramoodu as default
  userLocation = [76.909569, 8.682756]; // Venjaramoodu, Kerala
  setupMap(userLocation);
  createDestinationSuggestions();
}

function setupMap(center) {
  map = new mapboxgl.Map({
    container: "map",
    style: "mapbox://styles/mapbox/streets-v11",
    center: center,
    zoom: 12 // Increased zoom level for better local view
  });

  const nav = new mapboxgl.NavigationControl();
  map.addControl(nav);

  directions = new MapboxDirections({
    accessToken: mapboxgl.accessToken,
    unit: 'metric',
    profile: 'mapbox/driving',
    alternatives: true,
    controls: {
      inputs: true,
      instructions: true,
      profileSwitcher: true
    }
  });

  map.addControl(directions, "top-left");

  userMarker = new mapboxgl.Marker({ 
    color: 'blue'
  })
    .setLngLat(center)
    .addTo(map);

  map.on('load', () => {
    // Add a marker for current location with a popup
    new mapboxgl.Popup({ offset: 25 })
      .setLngLat(center)
      .setHTML('<h3>Your Current Location</h3>')
      .addTo(map);
  });
}

function startLocationTracking() {
  // Stop any existing watch
  if (watchId) {
    navigator.geolocation.clearWatch(watchId);
  }

  watchId = navigator.geolocation.watchPosition(
    updatePosition,
    (error) => console.error("Error watching position:", error),
    { 
      enableHighAccuracy: true,
      timeout: 10000,
      maximumAge: 0
    }
  );
}

function updatePosition(position) {
  userLocation = [position.coords.longitude, position.coords.latitude];
  userMarker.setLngLat(userLocation);
  // Don't automatically recenter map when tracking to allow user to explore
  // map.setCenter(userLocation);
}

function createDestinationSuggestions() {
  // Remove existing suggestions container if it exists
  const existingContainer = document.getElementById('destination-suggestions');
  if (existingContainer) {
    existingContainer.remove();
  }

  // Create a suggestions container
  const suggestionsContainer = document.createElement('div');
  suggestionsContainer.id = 'destination-suggestions';
  suggestionsContainer.style.cssText = `
    position: absolute;
    bottom: 20px;
    left: 20px;
    background: white;
    border-radius: 8px;
    padding: 15px;
    max-width: 300px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    z-index: 1;
    max-height: 300px;
    overflow-y: auto;
  `;

  const title = document.createElement('h3');
  title.textContent = 'Destinations in Kerala';
  title.style.borderBottom = '1px solid #eee';
  title.style.paddingBottom = '10px';
  suggestionsContainer.appendChild(title);

  suggestedDestinations.forEach((dest, index) => {
    const destElement = document.createElement('div');
    destElement.style.cssText = `
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;
      cursor: pointer;
      padding: 10px;
      border-radius: 5px;
      transition: background-color 0.3s;
    `;
    destElement.innerHTML = `
      <div>
        <strong>${dest.name}</strong>
        <p style="font-size: 0.8em; color: #666; margin: 5px 0 0;">${dest.description}</p>
      </div>
      <button style="background-color: #4CAF50; color: white; border: none; padding: 5px 10px; border-radius: 3px;">Navigate</button>
    `;
    
    destElement.querySelector('button').addEventListener('click', () => {
      // Calculate distance from current location
      const from = turf.point(userLocation);
      const to = turf.point(dest.coordinates);
      const distance = turf.distance(from, to, {units: 'kilometers'});

      // Set route
      directions.setOrigin(userLocation);
      directions.setDestination(dest.coordinates);
      
      // Zoom and center the map on the route
      map.fitBounds([
        userLocation,
        dest.coordinates
      ], {
        padding: 100
      });

      // Show distance information
      alert(`Distance to ${dest.name}: ${distance.toFixed(2)} km`);
    });

    destElement.addEventListener('mouseover', () => {
      destElement.style.backgroundColor = '#f0f0f0';
    });

    destElement.addEventListener('mouseout', () => {
      destElement.style.backgroundColor = 'transparent';
    });

    suggestionsContainer.appendChild(destElement);
  });

  // Add the suggestions container to the map
  map.getContainer().appendChild(suggestionsContainer);
}

// Add Turf.js for distance calculations
const script = document.createElement('script');
script.src = 'https://unpkg.com/@turf/turf@6/turf.min.js';
script.onload = initMap;
document.head.appendChild(script);