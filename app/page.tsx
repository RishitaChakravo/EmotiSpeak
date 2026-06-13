'use client'

import axios from "axios";
import { useState } from "react";
import { useRef, useEffect } from "react";

type Results = {
  audio?: {
    transcript?: String,
    word_count?: number,
    wpm?: number,
    fillers?: [string],
    filler_ratio?: number,
    filler_percentage?: number
  }
  video?: {
    dominant_emotion?: [string, number][];
    positive_ratio?: number;
    negative_ratio?: number;
    neutral_ratio?: number;
    confidence_level?: string;
  };
};

export default function Home() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [started, setStarted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<Results | null>(null);

  const startcamera = async () => {
    try {
      setResults(null);
      const res = await axios.post("http://localhost:8000/api/audioops/start")
      
      const stream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: false
      });
      streamRef.current = stream;
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.onloadedmetadata = () => {
          setStarted(true);
        };
      }
    } catch (err) {
      console.error(err);
    }
  }

  const captureImage = async () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext("2d")
    if (!ctx) return

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
    canvas.toBlob(async (blob) => {
      if (!blob) return;

      const formdata = new FormData();

      formdata.append("file", blob, "frame.jpg");

      try {
        const res = await axios.post("http://localhost:8000/api/video/frame", formdata);
      } catch (err) {
        console.log(err);
      }
    }, "image/jpeg");
  }

  useEffect(() => {
    if (!started) return;

    const interval = setInterval(() => {
      captureImage();
    }, 1000)

    return () => clearInterval(interval);
  }, [started]);

  const stopCamera = async () => {
    setLoading(true);
    setStarted(false);
    streamRef.current?.getTracks().forEach((track) => track.stop());

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    try {
      const res = await axios.post("http://localhost:8000/api/audioops/stop");
      setResults(res.data);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  }

  const vid = results?.video;
  const aud = results?.audio;

  return (
    <div className="min-h-screen bg-zinc-950 flex items-center justify-center p-6">
      <div className="grid grid-cols-2 gap-4 w-full max-w-4xl">
        {/* Camera card */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-2xl overflow-hidden flex flex-col">
          <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-800">
            <span className="text-sm font-medium text-zinc-100">
              Camera feed
            </span>

            {started && (
              <span className="flex items-center gap-1.5 text-xs bg-emerald-950 text-emerald-400 px-2.5 py-1 rounded-full">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                Live
              </span>
            )}
          </div>

          <div className="flex-1 bg-zinc-950 min-h-72 relative">
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="w-full h-full object-cover"
            />

            <canvas
              ref={canvasRef}
              style={{ display: "none" }}
            />

            {!started && (
              <div className="absolute inset-0 flex items-center justify-center text-zinc-600">
                Position your face here
              </div>
            )}
          </div>

          <div className="flex gap-2 p-3 border-t border-zinc-800">
            <button
              onClick={startcamera}
              disabled={started || loading}
              className="flex-1 py-2 rounded-xl text-sm font-medium bg-emerald-600 text-white cursor-pointer hover:bg-emerald-700 transition-color duration-150 ease-in"
            >
              Start Session
            </button>

            <button
              onClick={stopCamera}
              disabled={!started || loading}
              className="flex-1 py-2 rounded-xl text-sm font-medium bg-red-600 text-white cursor-pointer hover:bg-red-700 transition-color duration-150 ease-in"
            >
              Stop
            </button>
          </div>
        </div>
        <div className="bg-zinc-900 border border-zinc-800 rounded-2xl overflow-hidden flex flex-col">
          <div className="px-4 py-3 border-b border-zinc-800 text-sm font-medium text-zinc-100">
            Analysis results
          </div>

          {!results ? (
            <div className="flex-1 flex items-center justify-center text-zinc-600 text-sm p-6 text-center">
              {loading
                ? "Analyzing your session..."
                : "Results will appear after you stop the session."}
            </div>
          ) : (
            <div className="flex-1 p-4 flex flex-col gap-3 overflow-y-auto">
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-zinc-800 rounded-xl p-3">
                  <p className="text-xs text-zinc-500 uppercase tracking-wide mb-1">Word per Minute</p>
                  <p className="text-lg font-medium text-zinc-100 capitalize">
                    {aud?.wpm} wpm
                  </p>
                </div>
                <div className="bg-zinc-800 rounded-xl p-3">
                  <p className="text-xs text-zinc-500 uppercase tracking-wide mb-1">Confidence</p>
                  <p className="text-lg font-medium text-zinc-100">
                    {vid?.confidence_level ?? "—"}
                  </p>
                </div>
              </div>

              {[{ label: "Fillers Percentage", value: aud?.filler_ratio ?? 0, color: "bg-red-600" },
              { label: "Positive", value: vid?.positive_ratio ?? 0, color: "bg-emerald-500" },
              { label: "Negative", value: vid?.negative_ratio ?? 0, color: "bg-red-500" },
              { label: "Neutral", value: vid?.neutral_ratio ?? 0, color: "bg-zinc-500" },
              ].map(({ label, value, color }) => (
                <div key={label} className="bg-zinc-800 rounded-xl p-3">
                  <div className="flex justify-between mb-2">
                    <span className="text-xs text-zinc-500 uppercase tracking-wide">{label}</span>
                    <span className="text-sm font-medium text-zinc-200">{Math.round(value * 100)}%</span>
                  </div>
                  <div className="h-1.5 bg-zinc-700 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${color} transition-all duration-700`}
                      style={{ width: `${value * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

      </div>
    </div>
  );
}

