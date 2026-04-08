// frontend/src/components/indoorMap/indoormap.jsx
import { MapContainer, GeoJSON, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { useEffect } from 'react';
import './indoormap.css';

function MapController({ bounds }) {
    const map = useMap();
    useEffect(() => {
        if (bounds && bounds.isValid()) {
            map.fitBounds(bounds);
            map.zoomIn(1);
        }
    }, [map, bounds]);
    return null;
}

export default function IndoorMap({ mapData, path, onRoomClick }) {
    if (!mapData) return <div>Loading map...</div>;

    const bounds = L.geoJSON(mapData.rooms).getBounds();

    return (
        <MapContainer
            crs={L.CRS.Simple}
            bounds={bounds}
            minZoom={-10}
            maxZoom={5}
            style={{ height: '100%', width: '100%', backgroundColor: '#ffffff' }}
            scrollWheelZoom
        >
            <MapController bounds={bounds} />

            <GeoJSON
                data={mapData.rooms}
                style={{ color: '#7c3aed', fillColor: '#ede9fe', fillOpacity: 0.5, weight: 1 }}
                onEachFeature={(feature, layer) => {
                    const id = feature.properties.ABC1ROOMS;
                    if (id) {
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