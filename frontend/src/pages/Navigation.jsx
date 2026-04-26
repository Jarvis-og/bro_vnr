// frontend/src/pages/navigation.jsx
import { useState } from 'react';
import IndoorMap from '../components/IndoorMap/IndoorMap.jsx';
import { useNavigation } from '../components/IndoorMap/useNavigation.js';
import { Link } from 'react-router-dom';

export default function NavigationPage() {
  const { mapData, roomList, path, error, loading, navigate, clearRoute } = useNavigation();
  const [start, setStart] = useState('');
  const [goal, setGoal] = useState('');

  const handleClear = () => {
    setStart('');
    setGoal('');
    clearRoute();
  };

  return (
    <section className='flex w-3/4 h-screen'>
      <aside className='flex flex-col w-1/3 gap-5 bg-slate-200 relative'>
        <h2 className='text-lg mt-14 mx-4 font-bold'>Indoor Navigation</h2>

        <input
          className='rounded-md bg-white p-2 mx-3 shadow-2xl'
          list="room-list" value={start}
          onChange={e => setStart(e.target.value)}
          placeholder="FROM e.g. P101"
        />

        <input
          className='rounded-md bg-white p-2 mx-3 shadow-2xl'
          list="room-list" value={goal}
          onChange={e => setGoal(e.target.value)}
          placeholder="TO e.g. P401"
        />

        <datalist id="room-list">
          {[...new Set(roomList)].map((r, index) => <option key={`${r}-${index}`} value={r} />)}
        </datalist>

        <div className="flex gap-2 mx-3">
          <button
            className='bg-slate-400 hover:bg-slate-500 cursor-pointer rounded-md p-2 flex-1 font-semibold shadow-2xl'
            onClick={() => navigate(start, goal)} disabled={loading || !start || !goal}>
            {loading ? 'Finding route...' : 'Navigate >'}
          </button>

          <button
            className='bg-red-200 hover:bg-red-300 text-red-800 cursor-pointer rounded-md p-2 font-semibold shadow-2xl'
            onClick={handleClear}>
            Clear
          </button>
        </div>

        {error && <p style={{ color: 'red' }} className="mx-4">{error}</p>}
      </aside>

      <main className="flex-1 h-full w-full">
        <IndoorMap
          mapData={mapData}
          path={path}
          onRoomClick={id => setStart(prev => prev ? goal !== id ? setGoal(id) || prev : prev : id)}
        />
      </main>
    </section>
  );
}