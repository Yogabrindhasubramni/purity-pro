import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [file, setFile] = useState(null);
  const [downloadLink, setDownloadLink] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
    setDownloadLink(null);  // Reset download link on new file selection
    setError(null);  // Reset any previous errors
  };

  const handleUpload = () => {
    if (!file) {
      setError('Please select a file to upload.');
      return;
    }

    setLoading(true);
    setError(null);  // Reset error state
    const formData = new FormData();
    formData.append('file', file);

    axios.post('http://localhost:5000/upload', formData)
      .then((response) => {
        const filename = response.data.filename;
        return axios.post('http://localhost:5000/process', { filename });
      })
      .then((response) => {
        const downloadUrl = window.URL.createObjectURL(new Blob([response.data], { type: 'text/csv' }));
        setDownloadLink(downloadUrl);
        setLoading(false);
      })
      .catch((error) => {
        console.error("Error during upload or processing:", error.response ? error.response.data : error.message);
        setError(error.response?.data?.error || 'An error occurred during file upload or processing. Please try again.');
        setLoading(false);
      });
  };

  return (
    <div className="app-container">
      <h1>Welcome to PurityPro</h1>
      <div className="upload-box">
        <input type="file" onChange={handleFileChange} />
        <button onClick={handleUpload} disabled={loading}>
          {loading ? 'Processing...' : 'Upload & Process File'}
        </button>
        {error && <p className="error-message">{error}</p>}
        {downloadLink && (
          <a href={downloadLink} download="processed_file.csv" className="download-link">
            Download Cleaned File
          </a>
        )}
      </div>
    </div>
  );
}

export default App;
