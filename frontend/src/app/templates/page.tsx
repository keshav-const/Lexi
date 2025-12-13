/* CREATED BY UOIONHHC */
'use client';

import { useState, useEffect } from 'react';
import { getTemplates, deleteTemplate, TemplateListItem } from '@/lib/api';

export default function TemplatesPage() {
    const [templates, setTemplates] = useState<TemplateListItem[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        loadTemplates();
    }, []);

    const loadTemplates = async () => {
        setIsLoading(true);
        setError(null);
        try {
            const data = await getTemplates();
            setTemplates(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load templates');
        } finally {
            setIsLoading(false);
        }
    };

    const handleDelete = async (templateId: string) => {
        if (!confirm('Are you sure you want to delete this template?')) return;

        try {
            await deleteTemplate(templateId);
            setTemplates(prev => prev.filter(t => t.template_id !== templateId));
        } catch (err) {
            alert(err instanceof Error ? err.message : 'Failed to delete template');
        }
    };

    const handleExport = (templateId: string, format: 'json' | 'csv') => {
        window.open(`http://localhost:8000/api/templates/${templateId}/export?format=${format}`, '_blank');
    };

    const handleDownload = (templateId: string) => {
        window.open(`http://localhost:8000/api/templates/${templateId}/markdown`, '_blank');
    };

    return (
        <div>
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                        Templates
                    </h1>
                    <p className="text-gray-600 dark:text-gray-400">
                        Manage your document templates
                    </p>
                </div>
                <a
                    href="/upload"
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                    + New Template
                </a>
            </div>

            {isLoading && (
                <div className="flex justify-center py-12">
                    <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
                </div>
            )}

            {error && (
                <div className="p-4 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-xl text-red-700 dark:text-red-300">
                    {error}
                </div>
            )}

            {!isLoading && !error && templates.length === 0 && (
                <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
                    <div className="text-6xl mb-4">📄</div>
                    <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                        No templates yet
                    </h3>
                    <p className="text-gray-600 dark:text-gray-400 mb-4">
                        Upload a document to create your first template
                    </p>
                    <a
                        href="/upload"
                        className="inline-block px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                    >
                        Upload Document
                    </a>
                </div>
            )}

            {!isLoading && templates.length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {templates.map((template) => (
                        <div
                            key={template.template_id}
                            className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 hover:shadow-lg transition-shadow"
                        >
                            <div className="flex justify-between items-start mb-3">
                                <h3 className="font-semibold text-gray-900 dark:text-white">
                                    {template.title}
                                </h3>
                                <span className="text-xs bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 px-2 py-1 rounded">
                                    {template.doc_type || 'other'}
                                </span>
                            </div>

                            <div className="flex gap-1 mb-3 flex-wrap">
                                {template.similarity_tags.slice(0, 4).map((tag, i) => (
                                    <span
                                        key={i}
                                        className="text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 px-2 py-0.5 rounded"
                                    >
                                        {tag}
                                    </span>
                                ))}
                                {template.similarity_tags.length > 4 && (
                                    <span className="text-xs text-gray-500">
                                        +{template.similarity_tags.length - 4} more
                                    </span>
                                )}
                            </div>

                            <div className="flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400 mb-4">
                                <span>{template.variable_count} variables</span>
                                {template.jurisdiction && <span>📍 {template.jurisdiction}</span>}
                            </div>

                            <div className="flex gap-2">
                                <button
                                    onClick={() => handleDownload(template.template_id)}
                                    className="flex-1 py-2 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 
                             rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                                >
                                    📥 Download
                                </button>
                                <button
                                    onClick={() => handleExport(template.template_id, 'json')}
                                    className="py-2 px-3 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 
                             rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                                    title="Export variables as JSON"
                                >
                                    {'{'}...{'}'}
                                </button>
                                <button
                                    onClick={() => handleDelete(template.template_id)}
                                    className="py-2 px-3 text-sm bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 
                             rounded hover:bg-red-200 dark:hover:bg-red-800/50 transition-colors"
                                    title="Delete template"
                                >
                                    🗑
                                </button>
                            </div>

                            <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
                                <code className="text-xs text-gray-500 dark:text-gray-400 font-mono">
                                    {template.template_id}
                                </code>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
