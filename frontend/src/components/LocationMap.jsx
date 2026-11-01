import { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// Fix default marker icons under bundlers (Vite).
import iconUrl from "leaflet/dist/images/marker-icon.png";
import iconRetinaUrl from "leaflet/dist/images/marker-icon-2x.png";
import shadowUrl from "leaflet/dist/images/marker-shadow.png";

L.Icon.Default.mergeOptions({
  iconUrl,
  iconRetinaUrl,
  shadowUrl,
});

/**
 * Lightweight Leaflet wrapper around OpenStreetMap. Lazily creates the map once,
 * then moves the marker whenever latitude/longitude change.
 */
export default function LocationMap({ latitude, longitude, label }) {
  const containerRef = useRef(null);
  const mapRef = useRef(null);
  const markerRef = useRef(null);

  // Create the map a single time.
  useEffect(() => {
    if (mapRef.current || !containerRef.current) return;
    mapRef.current = L.map(containerRef.current, {
      zoomControl: true,
      attributionControl: true,
    }).setView([20, 0], 2);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(mapRef.current);

    // Invalidate size shortly after mount so tiles fill the container.
    const t = setTimeout(() => mapRef.current?.invalidateSize(), 150);
    return () => {
      clearTimeout(t);
      mapRef.current?.remove();
      mapRef.current = null;
      markerRef.current = null;
    };
  }, []);

  // Update marker/center when coordinates arrive.
  useEffect(() => {
    if (!mapRef.current || latitude == null || longitude == null) return;
    const latlng = [latitude, longitude];
    if (markerRef.current) {
      markerRef.current.setLatLng(latlng);
    } else {
      markerRef.current = L.marker(latlng).addTo(mapRef.current);
    }
    if (label) {
      markerRef.current.bindPopup(label);
    }
    mapRef.current.setView(latlng, 15);
  }, [latitude, longitude, label]);

  return <div className="location-map" ref={containerRef} role="img" aria-label="Map showing your current location" />;
}
