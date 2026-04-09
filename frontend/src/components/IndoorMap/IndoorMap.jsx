// frontend/src/components/indoorMap/indoormap.jsx
import { MapContainer, GeoJSON, useMap, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { useEffect, useMemo } from 'react'; // <-- Add useMemo here
import './indoormap.css';

const LABEL_ZOOM_THRESHOLD = -14; 

function MapController({ bounds }) {
    const map = useMap();
    useEffect(() => {
        if (bounds && bounds.isValid()) {
            map.fitBounds(bounds, { padding: [20, 20] });
        }
    }, [map, bounds]); // Because bounds is memoized, this now only runs ONCE.
    return null;
}

function ZoomHandler() {
    const map = useMapEvents({
        zoomend: () => {
            const currentZoom = map.getZoom();
            const container = map.getContainer();
            if (currentZoom <= LABEL_ZOOM_THRESHOLD) {
                container.classList.add('hide-labels');
            } else {
                container.classList.remove('hide-labels');
            }
        }
    });

    useEffect(() => {
        if (map.getZoom() <= LABEL_ZOOM_THRESHOLD) {
            map.getContainer().classList.add('hide-labels');
        }
    }, [map]);

    return null;
}

export default function IndoorMap({ mapData, path, onRoomClick }) {
    if (!mapData) return <div>Loading map...</div>;

    // useMemo stops the map from recalculating its size on every single click
    const bounds = useMemo(() => {
        return L.geoJSON(mapData.rooms).getBounds().pad(0.05);
    }, [mapData]);

    return (
        <MapContainer
            crs={L.CRS.Simple}
            bounds={bounds}
            minZoom={-16} // Stops it from zooming out into infinity
            maxZoom={5}
            maxBounds={bounds} // Keeps the panning locked to your building
            maxBoundsViscosity={1.0} 
            attributionControl={false} 
            style={{ height: '100%', width: '100%', backgroundColor: '#ffffff' }}
            scrollWheelZoom
        >
            <MapController bounds={bounds} />
            <ZoomHandler />

            <GeoJSON
                data={mapData.rooms}
                style={{ color: '#7c3aed', fillColor: '#ede9fe', fillOpacity: 0.5, weight: 1 }}
                onEachFeature={(feature, layer) => {
                    const rawId = feature.properties.ABC1ROOMS;
                    if (rawId) {
                        const id = String(rawId).replace(/\s+/g, '');
                        layer.bindTooltip(id, { 
                            permanent: true, 
                            direction: 'center',
                            className: 'room-label'
                        });
                        layer.on('click', () => onRoomClick?.(id));
                    }
                }}
            />

            <GeoJSON
                data={mapData.corridors}
                style={{ color: '#94a3b8', fillOpacity: 0.15, weight: 0.5 }}
            />

            <GeoJSON
                data={mapData.restricted}
                style={{ color: '#ef4444', fillColor: '#fee2e2', fillOpacity: 0.3, weight: 1, dashArray: '4 4' }}
            />

            {path?.path_geojson && (
                <GeoJSON
                    key={path.path_node_ids.join('-')}
                    data={path.path_geojson}
                    style={{ color: '#ef4444', weight: 5, opacity: 0.9 }}
                />
            )}
        </MapContainer>
    );
}