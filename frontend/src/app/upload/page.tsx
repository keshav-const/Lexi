/* CREATED BY UOIONHHC */
'use client';

import { useState } from 'react';
import FileUpload from '@/components/FileUpload';
import VariableReview from '@/components/VariableReview';
import { createTemplate } from '@/lib/api';

interface UploadData {
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
}

export default function UploadPage() {
    const [uploadData, setUploadData] = useState<UploadData | null>(null);
    const [isUploading, setIsUploading] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<{ templateId: string; title: string } | null>(null);

    const handleUploadStart = () => {
        setIsUploading(true);
        setError(null);
        setUploadData(null);
        setSuccess(null);
    };

    const handleUploadComplete = (data: UploadData) => {
        setUploadData(data);
        setIsUploading(false);
    };

    const handleError = (errorMessage: string) => {
        setError(errorMessage);
        setIsUploading(false);
    };

    const handleSave = async (data: {
        title: string;
        docType: string;
        tags: string[];
        variables: UploadData['variables'];
        bodyMd: string;
    }) => {
        setIsSaving(true);
        setError(null);

        try {
            const template = await createTemplate({
                title: data.title,
                body_md: data.bodyMd,
                variables: data.variables,
                doc_type: data.docType,
                similarity_tags: data.tags,
            });

            setSuccess({
                templateId: template.template_id,
                title: template.title,
            });
            setUploadData(null);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to save template');
        } finally {
            setIsSaving(false);
        }
    };

    const handleCancel = () => {
        setUploadData(null);
        setError(null);
    };

    const handleReset = () => {
        setUploadData(null);
        setSuccess(null);
        setError(null);
    };

    return (
        <div>
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                    Upload Document
                </h1>
                <p className="text-gray-600 dark:text-gray-400">
                    Upload a .docx or .pdf file to create a reusable template with {{`{{variables}}`}}.
                </p>
            </div>

            {/* Error Message */}
            {error && (
                <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-xl">
                    <div className="flex items-center gap-2 text-red-700 dark:text-red-300">
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span className="font-medium">{error}</span>
                    </div>
                </div>
            )}

            {/* Success Message */}
            {success && (
                <div className="mb-6 p-6 bg-green-50 dark:bg-green-900/30 border border-green-200 dark:border-green-800 rounded-xl">
                    <div className="flex items-start gap-3">
                        <div className="text-2xl">✅</div>
                        <div className="flex-1">
                            <h3 className="font-semibold text-green-700 dark:text-green-300 mb-1">
                                Template saved successfully!
                            </h3>
                            <p className="text-green-600 dark:text-green-400 text-sm mb-3">
                                <strong>{success.title}</strong> has been saved with ID: <code className="bg-green-100 dark:bg-green-800 px-1 rounded">{success.templateId}</code>
                            </p>
                            <div className="flex gap-3">
                                <a
                                    href="/templates"
                                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm"
                                >
                                    View in Templates
                                </a>
                                <button
                                    onClick={handleReset}
                                    className="px-4 py-2 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors text-sm"
                                >
                                    Upload Another
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Upload or Review */}
            {!success && (
                <>
                    {!uploadData ? (
                        <FileUpload
                            onUploadStart={handleUploadStart}
                            onUploadComplete={handleUploadComplete}
                            onError={handleError}
                        />
                    ) : (
                        <VariableReview
                            variables={uploadData.variables}
                            suggestedTitle={uploadData.suggested_title}
                            suggestedDocType={uploadData.suggested_doc_type}
                            similarityTags={uploadData.similarity_tags}
                            extractedTextPreview={uploadData.extracted_text_preview}
                            onSave={handleSave}
                            onCancel={handleCancel}
                            isSaving={isSaving}
                        />
                    )}
                </>
            )}

            {/* How it works */}
            {!uploadData && !success && (
                <div className="mt-12">
                    <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                        How it works
                    </h2>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div className="p-6 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
                            <div className="text-3xl mb-3">📤</div>
                            <h3 className="font-semibold text-gray-900 dark:text-white mb-2">1. Upload</h3>
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                                Upload your .docx or .pdf document
                            </p>
                        </div>
                        <div className="p-6 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
                            <div className="text-3xl mb-3">🔍</div>
                            <h3 className="font-semibold text-gray-900 dark:text-white mb-2">2. Extract</h3>
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                                AI identifies variables like names, dates, amounts
                            </p>
                        </div>
                        <div className="p-6 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
                            <div className="text-3xl mb-3">💾</div>
                            <h3 className="font-semibold text-gray-900 dark:text-white mb-2">3. Save</h3>
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                                Review and save as a reusable template
                            </p>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
