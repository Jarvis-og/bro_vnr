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
    <div className='flex w-full h-screen'>
      <div className='flex flex-col w-1/4 gap-5 bg-slate-100 relative'>
        <Link to="/">
          <button className="cursor-pointer text-2xl m-2 font-bold absolute">{`<`}</button>
        </Link>
        <h2 className='text-lg mt-14 mx-4'>Indoor Navigation</h2>

        <input
          className='rounded-md bg-white p-2 mx-2'
          list="room-list" value={start}
          onChange={e => setStart(e.target.value)}
          placeholder="FROM e.g. P101"
        />

        <input
          className='rounded-md bg-white p-2 mx-2'
          list="room-list" value={goal}
          onChange={e => setGoal(e.target.value)}
          placeholder="TO e.g. P401"
        />

        <datalist id="room-list">
          {[...new Set(roomList)].map((r, index) => <option key={`${r}-${index}`} value={r} />)}
        </datalist>

        <div className="flex gap-2 mx-2">
          <button
            className='bg-slate-200 hover:bg-slate-300 rounded-md p-2 flex-1'
            onClick={() => navigate(start, goal)} disabled={loading || !start || !goal}>
            {loading ? 'Finding route...' : 'Navigate >'}
          </button>
          
          <button
            className='bg-red-200 hover:bg-red-300 text-red-800 rounded-md p-2 font-semibold'
            onClick={handleClear}>
            Clear
          </button>
        </div>

        {error && <p style={{ color: 'red' }} className="mx-4">{error}</p>}
      </div>

      <div className="flex-1 h-full w-full">
        <IndoorMap
          mapData={mapData}
          path={path}
          onRoomClick={id => setStart(prev => prev ? goal !== id ? setGoal(id) || prev : prev : id)}
        />
      </div>
    </div>
  );
}