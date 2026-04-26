import React from 'react'
import { NavLink } from 'react-router-dom'

import { FaHome } from "react-icons/fa";
import { TbMessageChatbotFilled } from "react-icons/tb";
import { GiDirectionSigns } from "react-icons/gi";

const Sidebar = () => {
  const linkClass = "cursor-pointer text-4xl bg-white rounded-full p-6 shadow-2xl";
  return (
    <div className='w-1/4 bg-slate-200  flex flex-col justify-between items-center'>
      <div className='my-16 flex flex-col items-center justify-between flex-1'>
        <NavLink to="/">
          <button className={linkClass}><FaHome /></button>
        </NavLink>
        <NavLink to="/assistant">
          <button className={linkClass}><TbMessageChatbotFilled /></button>
        </NavLink>
        <NavLink to="/navigation">
          <button className={linkClass}><GiDirectionSigns /></button>
        </NavLink>
      </div>
      <NavLink to="/admin" className="w-full text-center bg-slate-300">
        <button className='rounded-2xl my-2 cursor-pointer text-lg font-bold'>Are you Admin?</button>
      </NavLink>
    </div>
  )
}

export default Sidebar
