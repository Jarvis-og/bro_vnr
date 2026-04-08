import React, { useState, useRef, useCallback } from 'react';
import { Link } from 'react-router-dom';
import Webcam from 'react-webcam';
import axios from 'axios';

const AdminPanel = () => {
  const webcamRef = useRef(null);

  // State for Authentication
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [adminPassInput, setAdminPassInput] = useState('');
  const [uploadingImages, setUploadingImages] = useState(false);

  // State for Enrollment
  const [personName, setPersonName] = useState('');
  const [capturedPhotos, setCapturedPhotos] = useState([]);

  // 1. Simple Access Check
  const handleLogin = (e) => {
    e.preventDefault();
    // In production, this should ideally be a backend check
    if (adminPassInput === "password") {
      setIsAuthenticated(true);
    } else {
      alert("Incorrect Admin Password");
    }
  };

  const capturePhoto = useCallback(() => {
    const imageSrc = webcamRef.current.getScreenshot();
    fetch(imageSrc)
      .then(res => res.blob())
      .then(blob => {
        if (capturedPhotos.length < 5) {
          setCapturedPhotos(prev => [...prev, blob]);
        } else {
          alert("Maximum 5 photos reached.");
        }
      });
  }, [webcamRef, capturedPhotos]);

  const handleUpload = async () => {
    if (!personName || capturedPhotos.length === 0) return alert("Missing info");

    const formData = new FormData();
    // We send the password again to the backend for the actual API security
    formData.append("password", adminPassInput);
    formData.append("person_name", personName);

    capturedPhotos.forEach((blob, i) => {
      formData.append("files", blob, `${personName}_${i}.jpg`);
    });

    try {
      setUploadingImages(true);
      const res = await axios.post("http://localhost:8000/admin/upload", formData);
      alert(res.data.message);
      setCapturedPhotos([]);
    } catch (err) {
      alert("Error: " + (err.response?.data?.detail || "Server error"));
    } finally {
      setUploadingImages(false);
    }
  };

  // --- VIEW 1: LOGIN SCREEN ---
  if (!isAuthenticated) {
    return (
      <>
        <Link to="/">
          <button className="cursor-pointer text-2xl font-bold m-2">{`<`}</button>
        </Link>
        <div className="flex flex-col items-center justify-center h-screen w-3/4">
          <div className="p-8 bg-white shadow-lg rounded-lg">
            <h2 className="text-2xl font-bold mb-4">Admin Login</h2>
            <form onSubmit={handleLogin} className="flex flex-col gap-4">
              <input
                type="password"
                placeholder="Enter Admin Password"
                className="border p-2 rounded"
                value={adminPassInput}
                onChange={e => setAdminPassInput(e.target.value)}
              />
              <button type="submit" className="bg-blue-600 text-white p-2 rounded cursor-pointer">
                Access Admin Panel
              </button>
            </form>
          </div>
        </div>
      </>
    );
  }

  // --- VIEW 2: ADMIN TOOLS ---
  return (
    <div className='text-center w-3/4 m-auto p-10'>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-bold">Admin Enrollment Mode</h2>
        <button onClick={() => setIsAuthenticated(false)} className="text-red-500 text-sm underline">Logout</button>
      </div>

      <Webcam
        ref={webcamRef}
        screenshotFormat="image/jpeg"
        width={400}
        className='m-auto rounded-lg shadow-md'
      />

      <div className="my-4 flex flex-col gap-2 max-w-xs m-auto">
        <input
          type="text"
          placeholder="Enter Person Name"
          className="border p-2 rounded"
          onChange={e => setPersonName(e.target.value)}
        />
        <button
          onClick={capturePhoto}
          className='bg-green-600 text-white p-2 rounded cursor-pointer'
        >
          Capture Photo ({capturedPhotos.length}/5)
        </button>
      </div>

      <div style={{ display: 'flex', justifyContent: 'center', gap: '10px', margin: '20px' }}>
        {capturedPhotos.map((_, i) => (
          <div key={i} className="w-12 h-12 bg-green-500 rounded-full flex items-center justify-center text-white text-xs">
            {i + 1}
          </div>
        ))}
      </div>

      <button
        onClick={handleUpload}
        disabled={capturedPhotos.length === 0 || uploadingImages}
        className={`p-3 rounded-lg w-full max-w-xs cursor-pointer ${capturedPhotos.length === 0 ? 'bg-gray-300' : 'bg-blue-700 text-white'}`}
      >
        Upload All Photos to Server
      </button>
    </div>
  );
};

export default AdminPanel;
