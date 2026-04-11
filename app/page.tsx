'use client'

import axios from "axios";
import { useState } from "react";

type Results = {
  audio?: {
    transcript?: String,
    word_count? : number,
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
  const [started, setStarted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<Results | null>(null);

  async function startRecording() {
    setLoading(true);
    setResults(null);
    await axios.post('http://localhost:8000/api/audioops/start');
    setStarted(true);
    setLoading(false);
  }

  async function stopRecording() {
    setLoading(true);
    const res = await axios.post('http://localhost:8000/api/audioops/stop');
    setResults(res.data);
    setStarted(false);
    setLoading(false);
    console.log(res.data?.audio?.transcript);
    console.log(res.data?.audio?.word_count);
    console.log(res.data?.audio?.fillers?.total);
  }

  const vid = results?.video;
  const aud = results?.audio;

  return (
    <div className="min-h-screen bg-zinc-950 flex items-center justify-center p-6">
      <div className="grid grid-cols-2 gap-4 w-full max-w-4xl">

        {/* Camera card */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-2xl overflow-hidden flex flex-col">
          <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-800">
            <span className="text-sm font-medium text-zinc-100">Camera feed</span>
            {started && (
              <span className="flex items-center gap-1.5 text-xs bg-emerald-950 text-emerald-400 px-2.5 py-1 rounded-full">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                Live
              </span>
            )}
          </div>

          <div className="flex-1 bg-zinc-950 flex items-center justify-center min-h-72 relative">
            {loading && (
              <div className="flex flex-col items-center gap-3 text-zinc-500">
                <div className="w-8 h-8 border-2 border-zinc-600 border-t-zinc-200 rounded-full animate-spin" />
                <span className="text-sm">Connecting...</span>
              </div>
            )}
            {!loading && started && (
              <img
                src="http://localhost:8000/api/video/stream"
                alt="Camera feed"
                className="w-full h-full object-cover"
              />
            )}
            {!loading && !started && (
              <div className="flex flex-col items-center gap-3 text-zinc-600">
                <div className="w-14 h-14 rounded-full border-2 border-dashed border-zinc-700 flex items-center justify-center">
                  <svg className="w-7 h-7" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
                    <circle cx="12" cy="8" r="4" />
                    <path d="M4 20c0-4 3.6-7 8-7s8 3 8 7" />
                  </svg>
                </div>
                <span className="text-sm">Position your face here</span>
              </div>
            )}
          </div>

          <div className="flex gap-2 p-3 border-t border-zinc-800">
            <button
              onClick={startRecording}
              disabled={started || loading}
              className="flex-1 py-2 rounded-xl text-sm font-medium bg-emerald-600 text-white disabled:opacity-30 hover:bg-emerald-500 transition-colors cursor-pointer"
            >
              Start session
            </button>
            <button
              onClick={stopRecording}
              disabled={!started || loading}
              className="flex-1 py-2 rounded-xl text-sm font-medium bg-red-600 text-white disabled:opacity-30 hover:bg-red-500 transition-colors cursor-pointer"
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

              {[{label: "Fillers Percentage", value: aud?.filler_ratio ?? 0, color: "bg-red-600"},
                { label: "Positive", value: vid?.positive_ratio ?? 0, color: "bg-emerald-500" },
                { label: "Negative", value: vid?.negative_ratio ?? 0, color: "bg-red-500" },
                { label: "Neutral",  value: vid?.neutral_ratio  ?? 0, color: "bg-zinc-500" },
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