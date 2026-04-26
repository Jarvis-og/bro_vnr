import React, { useState, useRef, useCallback } from 'react';
import { Link } from 'react-router-dom';
import Webcam from 'react-webcam';
import axios from 'axios';

const RAG_API = "http://localhost:8000";

const AdminPanel = () => {
  const webcamRef = useRef(null);

  // State for Authentication
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [adminPassInput, setAdminPassInput] = useState('');
  const [uploadingImages, setUploadingImages] = useState(false);

  // State for Enrollment
  const [personName, setPersonName] = useState('');
  const [capturedPhotos, setCapturedPhotos] = useState([]);

  // State for RAG controls
  const [setupStatus, setSetupStatus] = useState(null);   // null | 'loading' | 'success' | 'error'
  const [setupMsg, setSetupMsg] = useState('');
  const [ingestStatus, setIngestStatus] = useState(null);
  const [ingestMsg, setIngestMsg] = useState('');

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

  // RAG handlers
  const handleSetup = async () => {
    setSetupStatus('loading');
    setSetupMsg('');
    try {
      const res = await axios.post(`${RAG_API}/setup`);
      setSetupStatus('success');
      setSetupMsg(res.data.message);
    } catch (err) {
      setSetupStatus('error');
      setSetupMsg(err.response?.data?.detail || 'Setup failed');
    }
  };

  const handleIngest = async () => {
    setIngestStatus('loading');
    setIngestMsg('');
    try {
      const res = await axios.post(`${RAG_API}/ingest`);
      setIngestStatus('success');
      setIngestMsg(res.data.message);
    } catch (err) {
      setIngestStatus('error');
      setIngestMsg(err.response?.data?.detail || 'Ingestion failed');
    }
  };

  // --- VIEW 1: LOGIN SCREEN ---
  if (!isAuthenticated) {
    return (
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

      {/* ── RAG Knowledge Base Section ── */}
      <div className="mt-10 border-t pt-8">
        <h3 className="text-lg font-bold mb-1">Knowledge Base</h3>
        <p className="text-sm text-gray-500 mb-6">Set up and populate the RAG vector database</p>

        <div className="flex flex-col sm:flex-row gap-4 justify-center max-w-md m-auto">

          {/* Setup DB */}
          <div className="flex-1 border rounded-lg p-4 text-left">
            <p className="text-sm font-semibold mb-1">Step 1 · Setup Database</p>
            <p className="text-xs text-gray-400 mb-3">Initialize ChromaDB collection</p>
            <button
              onClick={handleSetup}
              disabled={setupStatus === 'loading'}
              className={`w-full p-2 rounded text-sm font-medium cursor-pointer transition-colors
                ${setupStatus === 'loading'
                  ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                  : 'bg-gray-800 text-white hover:bg-gray-700'}`}
            >
              {setupStatus === 'loading' ? 'Running…' : 'Run Setup'}
            </button>
            {setupMsg && (
              <p className={`mt-2 text-xs ${setupStatus === 'success' ? 'text-green-600' : 'text-red-500'}`}>
                {setupStatus === 'success' ? '✓ ' : '✗ '}{setupMsg}
              </p>
            )}
          </div>

          {/* Ingest */}
          <div className="flex-1 border rounded-lg p-4 text-left">
            <p className="text-sm font-semibold mb-1">Step 2 · Ingest Documents</p>
            <p className="text-xs text-gray-400 mb-3">Embed files from the data folder</p>
            <button
              onClick={handleIngest}
              disabled={ingestStatus === 'loading'}
              className={`w-full p-2 rounded text-sm font-medium cursor-pointer transition-colors
                ${ingestStatus === 'loading'
                  ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                  : 'bg-gray-800 text-white hover:bg-gray-700'}`}
            >
              {ingestStatus === 'loading' ? 'Ingesting…' : 'Run Ingestion'}
            </button>
            {ingestMsg && (
              <p className={`mt-2 text-xs ${ingestStatus === 'success' ? 'text-green-600' : 'text-red-500'}`}>
                {ingestStatus === 'success' ? '✓ ' : '✗ '}{ingestMsg}
              </p>
            )}
          </div>

        </div>
      </div>
      {/* ── End RAG Section ── */}

    </div>
  );
};

export default AdminPanel;