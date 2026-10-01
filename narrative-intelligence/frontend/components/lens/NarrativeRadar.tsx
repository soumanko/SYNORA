import React from 'react';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, ResponsiveContainer, Tooltip } from 'recharts';

interface NarrativeRadarProps {
  scores: Record<string, number>;
}

export default function NarrativeRadar({ scores }: NarrativeRadarProps) {
  // Map dimensions to a format Recharts understands
  const data = Object.entries(scores).map(([dimension, value]) => ({
    dimension,
    value: Math.max(0, Math.min(100, value * 100)), // scale 0-1 to 0-100
  }));

  if (data.length === 0) {
    // Provide a dummy shape if empty just for layout placeholder
    data.push(
      { dimension: "Agents", value: 65 },
      { dimension: "Social Networks", value: 50 },
      { dimension: "Style", value: 80 },
      { dimension: "Plot", value: 70 },
      { dimension: "Setting", value: 40 },
      { dimension: "Events", value: 60 },
      { dimension: "Revelation", value: 75 },
      { dimension: "Situatedness", value: 45 },
      { dimension: "Temporal", value: 85 },
      { dimension: "Perspective", value: 90 }
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
      <h3 className="text-lg font-semibold mb-6 text-center">Narrative Fingerprint</h3>
      <div className="h-[350px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart cx="50%" cy="50%" outerRadius="70%" data={data}>
            <PolarGrid stroke="#e5e7eb" />
            <PolarAngleAxis 
              dataKey="dimension" 
              tick={{ fill: '#4b5563', fontSize: 12 }} 
            />
            <Tooltip 
              formatter={(value: any) => [`${Number(value).toFixed(1)}%`, 'Activity']}
              contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
            />
            <Radar
              name="Document"
              dataKey="value"
              stroke="#2563eb"
              fill="#3b82f6"
              fillOpacity={0.4}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
