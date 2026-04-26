import React from 'react'
import FaceVerification from "../components/FaceVerification"

const Home = () => {
    return (
        <div className='w-3/4'>
            <h1 className="text-6xl text-center font-extrabold my-4">Buddy Robot On-Campus</h1>
            <h2 className='text-center text-xl font-semibold'>Welcome to the department of Electrical and Electronics Engineering</h2>
            <FaceVerification />
        </div>
    )
}

export default Home
