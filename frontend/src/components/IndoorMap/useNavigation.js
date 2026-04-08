// frontend/src/components/indoorMap/useNavigation.js
import { useState, useEffect } from 'react';

const BASE = 'http://localhost:8000/nav';

export function useNavigation() {
    const [mapData, setMapData]   = useState(null);
    const [roomList, setRoomList] = useState([]);
    const [path, setPath]         = useState(null);
    const [error, setError]       = useState(null);
    const [loading, setLoading]   = useState(false);

    useEffect(() => {
        Promise.all([
            fetch(`${BASE}/map-data`).then(r => r.json()),
            fetch(`${BASE}/rooms`).then(r => r.json()),
        ]).then(([map, rooms]) => {
            setMapData(map);
            setRoomList(rooms.rooms);
        });
    }, []);

    async function navigate(start, goal) {
        setLoading(true);
        setError(null);
        try {
            const res = await fetch(`${BASE}/navigate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ start, goal }),
            });
            const data = await res.json();
            if (!res.ok) { setError(data.error); return; }
            setPath(data);
        } finally {
            setLoading(false);
        }
    }

    function clearRoute() {
        setPath(null);
        setError(null);
    }

    return { mapData, roomList, path, error, loading, navigate, clearRoute };
}