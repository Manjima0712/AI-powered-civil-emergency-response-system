document.addEventListener('DOMContentLoaded', function() {
    if ("geolocation" in navigator) {
        navigator.geolocation.getCurrentPosition(function(position) {
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;
            
            // Reload page with coordinates
            window.location.href = `/?lat=${lat}&lon=${lon}`;
        }, function(error) {
            console.error('Error getting location:', error);
        });
    }
    
    // Refresh page every 5 minutes to get updated weather
    setInterval(function() {
        window.location.reload();
    }, 300000);
});