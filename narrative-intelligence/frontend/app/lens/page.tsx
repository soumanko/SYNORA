'use client';

import React, { useState } from 'react';
import DocumentUploader from '@/components/lens/DocumentUploader';
import ExecutiveSummary from '@/components/lens/ExecutiveSummary';
import NarrativeRadar from '@/components/lens/NarrativeRadar';
import CoreFeatureChart from '@/components/lens/CoreFeatureChart';
import { analyzeDocument } from '@/lib/api';
import { NarrativeProfile } from '@/lib/types';
import { Loader2 } from 'lucide-react';

export default function LensPage() {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [profile, setProfile] = useState<NarrativeProfile | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  // Progress stages
  const [stage, setStage] = useState(0);
  
  const stages = [
    "Preparing document",
    "Extracting narrative features",
    "Building feature representation",
    "Running statistical analysis",
    "Building narrative profile",
    "Preparing visualizations"
  ];

  const handleDocumentSelected = async (text: string, filename: string) => {
    setIsAnalyzing(true);
    setError(null);
    setProfile(null);
    setStage(0);
    
    // Simulate progress updates while API is running
    const progressInterval = setInterval(() => {
      setStage(s => Math.min(s + 1, stages.length - 2));
    }, 1500);

    try {
      const res = await analyzeDocument(text, filename);
      
      clearInterval(progressInterval);
      setStage(stages.length - 1);
      
      if (res.status === 'error' || res.status === 'failed') {
        if (res.error) {
          throw new Error(`[${res.error.code}] ${res.error.message}`);
        }
        throw new Error(res.message || "Failed to analyze document");
      }
      
      if (res.narrative_profile) {
        if (!res.narrative_profile.core30_features || !res.narrative_profile.core30_features.features) {
          throw new Error("Backend returned an incomplete NarrativeProfile (missing core30_features). Endpoint may be a stub.");
        }
        setProfile(res.narrative_profile);
      } else {
        throw new Error("No narrative profile returned from server");
      }
    } catch (err) {
      clearInterval(progressInterval);
      setError(err instanceof Error ? err.message : "An unknown error occurred");
    } finally {
      setTimeout(() => setIsAnalyzing(false), 500);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50/50 pb-20">
      <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between sticky top-0 z-10">
        <div className="font-bold text-xl tracking-tight">NARRATIVE LENS</div>
        {profile && (
          <button 
            onClick={() => setProfile(null)}
            className="text-sm font-medium text-gray-500 hover:text-gray-900"
          >
            New Analysis
          </button>
        )}
      </header>

      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {!isAnalyzing && !profile && !error && (
          <DocumentUploader onDocumentSelected={handleDocumentSelected} />
        )}

        {error && (
          <div className="max-w-3xl mx-auto mt-12 bg-red-50 border border-red-200 text-red-800 p-6 rounded-xl shadow-sm">
            <h3 className="font-semibold text-lg mb-2">Analysis Failed</h3>
            <p className="text-red-700">{error}</p>
            <button 
              onClick={() => setError(null)}
              className="mt-6 bg-white border border-red-200 text-red-700 px-4 py-2 rounded-md font-medium hover:bg-red-50"
            >
              Try Again
            </button>
          </div>
        )}

        {isAnalyzing && (
          <div className="max-w-xl mx-auto mt-24 bg-white border border-gray-200 rounded-xl p-8 shadow-sm">
            <div className="flex items-center justify-center mb-8">
              <Loader2 className="h-10 w-10 text-blue-600 animate-spin" />
            </div>
            <div className="space-y-4">
              {stages.map((s, i) => (
                <div key={i} className={`flex items-center ${i > stage ? 'opacity-30' : 'opacity-100'}`}>
                  <div className={`h-5 w-5 rounded-full flex items-center justify-center mr-3 ${i < stage ? 'bg-green-500 text-white' : i === stage ? 'border-2 border-blue-500' : 'border-2 border-gray-300'}`}>
                    {i < stage && (
                      <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                      </svg>
                    )}
                  </div>
                  <span className={`text-sm ${i === stage ? 'font-medium text-blue-700' : 'text-gray-600'}`}>{s}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {profile && !isAnalyzing && (
          <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {profile.metadata?.analysis_mode === 'core' && (
              <div className="bg-blue-50 border border-blue-200 text-blue-800 px-4 py-3 rounded-lg shadow-sm">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3 flex-1 md:flex md:justify-between">
                    <p className="text-sm">
                      <strong>Development analysis</strong><br/>
                      This run analyzes the 30-feature Core Feature subset. Full 304-feature analysis is available when the configured provider quota permits it.
                    </p>
                  </div>
                </div>
              </div>
            )}
            
            <ExecutiveSummary profile={profile} />
            
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              <div className="lg:col-span-1">
                {/* Fallback to mock dimensions if backend didn't supply them */}
                <NarrativeRadar scores={profile.metadata?.dimension_scores || {}} />
              </div>
              <div className="lg:col-span-2">
                <CoreFeatureChart core30={profile.core30_features} />
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
