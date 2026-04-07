'use client'

import axios from "axios";
import { useState } from "react";

export default function Home() {
  const [data, setData] = useState("");
  async function startrecording() {
    try {
      const res = await axios.post('http://localhost:8000/api/audioops/start')
      console.log(res.data)
      setData(res.data.status);
    } catch(e) {
      console.log("Error", e);
    }
  }
  const stoprecording = async() => {
    try{
      const res = await axios.post('http://localhost:8000/api/audioops/stop')
      const data = await res.data;
      setData(JSON.stringify(data));
      console.log(data);
    } catch(e) {
      console.log(e);
    }
  }
  return (
    <div className="flex align-center justify-center gap-1 h-full">
      <button onClick={startrecording}>Start</button>
      <button onClick={stoprecording}>Stop</button>
      <div>{data}</div>
    </div>
  );
}
