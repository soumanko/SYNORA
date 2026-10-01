import React from 'react';
import { FileText, AlertCircle } from 'lucide-react';
import { NarrativeProfile } from '@/lib/types';
import { formatProbability } from '@/lib/formatting';

interface ExecutiveSummaryProps {
  profile: NarrativeProfile;
  summaryText?: string;
}

export default function ExecutiveSummary({ profile, summaryText }: ExecutiveSummaryProps) {
  const classification = profile.classification;

  return (
    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
      <div className="border-b border-gray-100 bg-gray-50/50 p-4 px-6 flex justify-between items-center">
        <div>
          <h2 className="font-semibold text-lg flex items-center">
            <FileText className="h-5 w-5 mr-2 text-gray-500" />
            Analysis complete
          </h2>
          <div className="text-xs text-gray-500 mt-1 flex space-x-4">
            <span>Engine: NIE-0.1.0</span>
            <span>StoryScope: main</span>
            <span>Taxonomy: 304 features</span>
          </div>
        </div>
      </div>

      <div className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div>
            <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-4">
              Statistical alignment
            </h3>
            
            {classification ? (
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="font-medium">Human reference</span>
                    <span>{formatProbability(classification.human_probability)}</span>
                  </div>
                  <div className="w-full bg-gray-100 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full" 
                      style={{ width: `${classification.human_probability * 100}%` }}
                    ></div>
                  </div>
                </div>
                
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="font-medium">AI reference</span>
                    <span>{formatProbability(classification.ai_probability)}</span>
                  </div>
                  <div className="w-full bg-gray-100 rounded-full h-2">
                    <div 
                      className="bg-purple-600 h-2 rounded-full" 
                      style={{ width: `${classification.ai_probability * 100}%` }}
                    ></div>
                  </div>
                </div>

                <div className="pt-4 mt-4 border-t border-gray-100 text-xs text-gray-500">
                  <p>Model: {classification.model_version}</p>
                  <p>Feature set: {classification.feature_set}</p>
                </div>
              </div>
            ) : (
              <div className="text-gray-500 text-sm italic">
                Classification data unavailable for this document.
              </div>
            )}
          </div>
          
          <div>
            <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-4">
              Major narrative patterns
            </h3>
            <p className="text-sm text-gray-700 leading-relaxed">
              {summaryText || "The document exhibits narrative features consistent with its primary class alignment. Core diagnostic signals include temporal structuring, perspective consistency, and agent interaction density."}
            </p>
          </div>
        </div>

        <div className="mt-8 bg-amber-50 border border-amber-200 rounded-lg p-4 flex items-start">
          <AlertCircle className="h-5 w-5 text-amber-500 mr-3 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-amber-800">
            <p className="font-medium mb-1">Experimental extension</p>
            <p>StoryScope was developed and evaluated primarily on fiction. Results for academic papers, essays, news and other non-fiction material should be interpreted as exploratory rather than validated authorship evidence.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
