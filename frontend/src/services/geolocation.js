/**
 * Geolocation helpers built on the browser Geolocation API.
 * Returns Promises so callers can use async/await and catch failures.
 */

export function isGeolocationAvailable() {
  return typeof navigator !== "undefined" && "geolocation" in navigator;
}

/**
 * Resolve to { latitude, longitude, accuracy } or reject with an Error whose
 * message is human-friendly and already accounts for permission denial.
 */
export function getCurrentPosition(options = {}) {
  return new Promise((resolve, reject) => {
    if (!isGeolocationAvailable()) {
      reject(new Error("Location is not supported by this browser."));
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) =>
        resolve({
          latitude: pos.coords.latitude,
          longitude: pos.coords.longitude,
          accuracy: pos.coords.accuracy,
          timestamp: pos.timestamp,
        }),
      (err) => {
        let message;
        switch (err.code) {
          case err.PERMISSION_DENIED:
            message =
              "Location permission was denied. Enable location access in your browser settings to use this feature.";
            break;
          case err.POSITION_UNAVAILABLE:
            message = "Your current location is unavailable right now.";
            break;
          case err.TIMEOUT:
            message = "It took too long to get your location. Please try again.";
            break;
          default:
            message = "Could not determine your location.";
        }
        reject(new Error(message));
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0, ...options }
    );
  });
}

/** Build a shareable Google Maps link for the given coordinates. */
export function googleMapsUrl(latitude, longitude) {
  return `https://www.google.com/maps?q=${latitude},${longitude}`;
}
