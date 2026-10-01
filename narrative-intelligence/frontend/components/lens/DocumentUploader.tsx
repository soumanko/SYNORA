import React, { useState } from 'react';
import { UploadCloud, FileText, File as FileIcon } from 'lucide-react';

interface DocumentUploaderProps {
  onDocumentSelected: (text: string, filename: string, file: File | null) => void;
}

export default function DocumentUploader({ onDocumentSelected }: DocumentUploaderProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [textMode, setTextMode] = useState(false);
  const [pastedText, setPastedText] = useState('');

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const processFile = async (file: File) => {
    // For MVP, we just read text files. In a real app, parse PDF/DOCX
    const text = await file.text();
    onDocumentSelected(text, file.name, file);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      await processFile(file);
    }
  };

  const handleFileInput = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      await processFile(file);
    }
  };

  const handleTextSubmit = () => {
    if (pastedText.trim()) {
      onDocumentSelected(pastedText, 'pasted_text.txt', null);
    }
  };

  return (
    <div className="w-full max-w-3xl mx-auto mt-12">
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold tracking-tight mb-2">NARRATIVE LENS</h1>
        <p className="text-gray-500">Narrative analysis through discourse-level features</p>
      </div>

      {!textMode ? (
        <div 
          className={`border-2 border-dashed rounded-xl p-12 text-center transition-colors ${
            isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'
          }`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <div className="flex justify-center mb-4">
            <UploadCloud className="h-12 w-12 text-gray-400" />
          </div>
          <h3 className="text-lg font-medium mb-2">Drop your document here</h3>
          <p className="text-sm text-gray-500 mb-6">PDF · DOCX · TXT</p>
          
          <div className="flex items-center justify-center space-x-4">
            <label className="cursor-pointer bg-black text-white px-4 py-2 rounded-md font-medium hover:bg-gray-800 transition-colors">
              Browse Files
              <input type="file" className="hidden" accept=".txt,.pdf,.docx" onChange={handleFileInput} />
            </label>
            <span className="text-gray-400">or</span>
            <button 
              onClick={() => setTextMode(true)}
              className="text-black border border-gray-300 px-4 py-2 rounded-md font-medium hover:bg-gray-50 transition-colors"
            >
              Paste text
            </button>
          </div>
        </div>
      ) : (
        <div className="border border-gray-300 rounded-xl overflow-hidden shadow-sm">
          <div className="bg-gray-50 p-3 border-b border-gray-200 flex justify-between items-center">
            <div className="flex items-center text-sm font-medium text-gray-700">
              <FileText className="h-4 w-4 mr-2" />
              Paste Document Text
            </div>
            <button 
              onClick={() => setTextMode(false)}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              Cancel
            </button>
          </div>
          <textarea
            className="w-full h-64 p-4 focus:outline-none resize-y"
            placeholder="Paste your document text here..."
            value={pastedText}
            onChange={(e) => setPastedText(e.target.value)}
          />
          <div className="bg-gray-50 p-3 border-t border-gray-200 flex justify-end">
            <button
              onClick={handleTextSubmit}
              disabled={!pastedText.trim()}
              className="bg-black text-white px-6 py-2 rounded-md font-medium hover:bg-gray-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Confirm Text
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
