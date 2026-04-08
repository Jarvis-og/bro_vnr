import React from 'react'
import { NavLink } from 'react-router-dom'

const Sidebar = () => {
  return (
    <div className='w-1/4 bg-slate-100 flex flex-col items-center justify-around'>
      <NavLink to="/assistant">
        <button className='bg-white p-16 rounded-2xl cursor-pointer text-xl font-bold'>Assistant</button>
      </NavLink>
      <NavLink to="/navigation">
        <button className='bg-white p-16 rounded-2xl cursor-pointer text-xl font-bold'>Navigation</button>
      </NavLink>
      <NavLink to="/admin">
        <button className='bg-white p-16 rounded-2xl cursor-pointer text-xl font-bold'>Admin</button>
      </NavLink>
    </div>
  )
}

export default Sidebar
