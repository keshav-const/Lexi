/* CREATED BY UOIONHHC */
'use client';

import { useState } from 'react';

interface Variable {
    key: string;
    label: string;
    description?: string;
    example?: string;
    required: boolean;
    dtype: string;
}

interface VariableReviewProps {
    variables: Variable[];
    suggestedTitle: string;
    suggestedDocType: string;
    similarityTags: string[];
    extractedTextPreview: string;
    onSave: (data: {
        title: string;
        docType: string;
        tags: string[];
        variables: Variable[];
        bodyMd: string;
    }) => void;
    onCancel: () => void;
    isSaving: boolean;
}

export default function VariableReview({
    variables: initialVariables,
    suggestedTitle,
    suggestedDocType,
    similarityTags,
    extractedTextPreview,
    onSave,
    onCancel,
    isSaving,
}: VariableReviewProps) {
    const [title, setTitle] = useState(suggestedTitle);
    const [docType, setDocType] = useState(suggestedDocType);
    const [tags, setTags] = useState(similarityTags.join(', '));
    const [variables, setVariables] = useState(initialVariables);

    const handleVariableChange = (index: number, field: keyof Variable, value: string | boolean) => {
        setVariables(prevVars => {
            const newVars = [...prevVars];
            newVars[index] = { ...newVars[index], [field]: value };
            return newVars;
        });
    };

    const handleRemoveVariable = (index: number) => {
        setVariables(prevVars => prevVars.filter((_, i) => i !== index));
    };

    const handleSave = () => {
        // Generate template body with variables
        let bodyMd = extractedTextPreview;
        variables.forEach(v => {
            // Replace example values with template variables
            if (v.example) {
                bodyMd = bodyMd.replace(new RegExp(v.example, 'g'), `{{${v.key}}}`);
            }
        });

        onSave({
            title,
            docType,
            tags: tags.split(',').map(t => t.trim()).filter(t => t),
            variables,
            bodyMd,
        });
    };

    return (
        <div className="space-y-6">
            {/* Template Info */}
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg border border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Template Information</h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Title
                        </label>
                        <input
                            type="text"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg 
                         bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                         focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Document Type
                        </label>
                        <select
                            value={docType}
                            onChange={(e) => setDocType(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg 
                         bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                         focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        >
                            <option value="legal_notice">Legal Notice</option>
                            <option value="contract">Contract</option>
                            <option value="agreement">Agreement</option>
                            <option value="letter">Letter</option>
                            <option value="deed">Deed</option>
                            <option value="policy">Policy</option>
                            <option value="other">Other</option>
                        </select>
                    </div>

                    <div className="md:col-span-2">
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Tags (comma separated)
                        </label>
                        <input
                            type="text"
                            value={tags}
                            onChange={(e) => setTags(e.target.value)}
                            placeholder="insurance, notice, india"
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg 
                         bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                         focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                    </div>
                </div>
            </div>

            {/* Variables */}
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg border border-gray-200 dark:border-gray-700">
                <div className="flex justify-between items-center mb-4">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                        Detected Variables ({variables.length})
                    </h3>
                </div>

                <div className="space-y-4 max-h-96 overflow-y-auto">
                    {variables.map((variable, index) => (
                        <div
                            key={index}
                            className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg border border-gray-200 dark:border-gray-600"
                        >
                            <div className="flex justify-between items-start mb-3">
                                <div className="flex items-center gap-2">
                                    <code className="text-sm font-mono bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 px-2 py-0.5 rounded">
                                        {`{{${variable.key}}}`}
                                    </code>
                                    {variable.required && (
                                        <span className="text-xs bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300 px-2 py-0.5 rounded">
                                            Required
                                        </span>
                                    )}
                                    <span className="text-xs bg-gray-200 dark:bg-gray-600 text-gray-600 dark:text-gray-300 px-2 py-0.5 rounded">
                                        {variable.dtype}
                                    </span>
                                </div>
                                <button
                                    onClick={() => handleRemoveVariable(index)}
                                    className="text-red-500 hover:text-red-700 p-1"
                                >
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                    </svg>
                                </button>
                            </div>

                            <div className="grid grid-cols-2 gap-3">
                                <input
                                    type="text"
                                    value={variable.label}
                                    onChange={(e) => handleVariableChange(index, 'label', e.target.value)}
                                    placeholder="Label"
                                    className="px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded
                             bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                                />
                                <input
                                    type="text"
                                    value={variable.example || ''}
                                    onChange={(e) => handleVariableChange(index, 'example', e.target.value)}
                                    placeholder="Example value"
                                    className="px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded
                             bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                                />
                            </div>

                            {variable.description && (
                                <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                                    {variable.description}
                                </p>
                            )}
                        </div>
                    ))}

                    {variables.length === 0 && (
                        <p className="text-center text-gray-500 dark:text-gray-400 py-8">
                            No variables detected
                        </p>
                    )}
                </div>
            </div>

            {/* Actions */}
            <div className="flex justify-end gap-3">
                <button
                    onClick={onCancel}
                    disabled={isSaving}
                    className="px-4 py-2 text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 
                     rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                >
                    Discard
                </button>
                <button
                    onClick={handleSave}
                    disabled={isSaving || !title}
                    className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 
                     transition-colors disabled:opacity-50 disabled:cursor-not-allowed
                     flex items-center gap-2"
                >
                    {isSaving ? (
                        <>
                            <span className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full"></span>
                            Saving...
                        </>
                    ) : (
                        'Save Template'
                    )}
                </button>
            </div>
        </div>
    );
}
