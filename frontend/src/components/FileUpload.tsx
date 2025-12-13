/* CREATED BY UOIONHHC */
'use client';

import { useState, useRef } from 'react';

interface FileUploadProps {
    onUploadStart: () => void;
    onUploadComplete: (data: {
        filename: string;
        extracted_text_preview: string;
        variables: Array<{
            key: string;
            label: string;
            description?: string;
            example?: string;
            required: boolean;
            dtype: string;
        }>;
        suggested_title: string;
        suggested_doc_type: string;
        similarity_tags: string[];
    }) => void;
    onError: (error: string) => void;
}

export default function FileUpload({ onUploadStart, onUploadComplete, onError }: FileUploadProps) {
    const [isDragging, setIsDragging] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleDragEnter = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(true);
    };

    const handleDragLeave = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
    };

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
    };

    const handleDrop = async (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            await uploadFile(files[0]);
        }
    };

    const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = e.target.files;
        if (files && files.length > 0) {
            await uploadFile(files[0]);
        }
    };

    const uploadFile = async (file: File) => {
        const allowedTypes = [
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/pdf'
        ];
        const allowedExtensions = ['.docx', '.pdf'];

        const extension = file.name.toLowerCase().slice(file.name.lastIndexOf('.'));

        if (!allowedExtensions.includes(extension)) {
            onError('Please upload a .docx or .pdf file');
            return;
        }

        setIsUploading(true);
        onUploadStart();

        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('http://localhost:8000/api/upload', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Upload failed');
            }

            const data = await response.json();
            onUploadComplete(data);
        } catch (error) {
            onError(error instanceof Error ? error.message : 'Upload failed');
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <div
            className={`
        relative border-2 border-dashed rounded-xl p-8 text-center transition-all duration-300 cursor-pointer
        ${isDragging
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                    : 'border-gray-300 dark:border-gray-600 hover:border-blue-400 dark:hover:border-blue-500'
                }
        ${isUploading ? 'opacity-50 pointer-events-none' : ''}
      `}
            onDragEnter={handleDragEnter}
            onDragLeave={handleDragLeave}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
        >
            <input
                ref={fileInputRef}
                type="file"
                accept=".docx,.pdf"
                className="hidden"
                onChange={handleFileSelect}
            />

            <div className="space-y-4">
                <div className="mx-auto w-16 h-16 text-gray-400 dark:text-gray-500">
                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                </div>

                {isUploading ? (
                    <div className="space-y-3">
                        <div className="animate-spin mx-auto w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
                        <p className="text-gray-600 dark:text-gray-300">Processing document...</p>
                    </div>
                ) : (
                    <>
                        <div>
                            <p className="text-lg font-medium text-gray-700 dark:text-gray-200">
                                Drop your document here
                            </p>
                            <p className="text-sm text-gray-500 dark:text-gray-400">
                                or click to browse
                            </p>
                        </div>
                        <p className="text-xs text-gray-400 dark:text-gray-500">
                            Supports .docx and .pdf files (max 10MB)
                        </p>
                    </>
                )}
            </div>
        </div>
    );
}
