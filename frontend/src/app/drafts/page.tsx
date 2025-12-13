/* CREATED BY UOIONHHC */
'use client';

import { useState, useEffect } from 'react';
import { getDrafts, getDraft } from '@/lib/api';

interface DraftListItem {
    id: number;
    template_id: string;
    template_title: string;
    user_query: string;
    preview: string;
    created_at: string;
}

export default function DraftsPage() {
    const [drafts, setDrafts] = useState<DraftListItem[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedDraft, setSelectedDraft] = useState<{
        id: number;
        draft_md: string;
        template_title: string;
    } | null>(null);

    useEffect(() => {
        loadDrafts();
    }, []);

    const loadDrafts = async () => {
        setIsLoading(true);
        setError(null);
        try {
            const data = await getDrafts();
            setDrafts(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load drafts');
        } finally {
            setIsLoading(false);
        }
    };

    const handleView = async (draftId: number) => {
        try {
            const draft = await getDraft(draftId);
            setSelectedDraft({
                id: draft.id,
                draft_md: draft.draft_md,
                template_title: draft.template_title,
            });
        } catch (err) {
            alert('Failed to load draft');
        }
    };

    const handleDownload = (draft: { id: number; draft_md: string; template_title: string }) => {
        const blob = new Blob([draft.draft_md], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${draft.template_title.toLowerCase().replace(/\s+/g, '_')}_${draft.id}.md`;
        a.click();
        URL.revokeObjectURL(url);
    };

    const handleCopy = (text: string) => {
        navigator.clipboard.writeText(text);
        alert('Copied to clipboard!');
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleString();
    };

    return (
        <div>
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                    Draft History
                </h1>
                <p className="text-gray-600 dark:text-gray-400">
                    View and manage your generated documents
                </p>
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

            {!isLoading && !error && drafts.length === 0 && (
                <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
                    <div className="text-6xl mb-4">📝</div>
                    <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                        No drafts yet
                    </h3>
                    <p className="text-gray-600 dark:text-gray-400 mb-4">
                        Generate drafts from the chat interface
                    </p>
                    <a
                        href="/"
                        className="inline-block px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                    >
                        Start Drafting
                    </a>
                </div>
            )}

            {!isLoading && drafts.length > 0 && (
                <div className="space-y-4">
                    {drafts.map((draft) => (
                        <div
                            key={draft.id}
                            className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6"
                        >
                            <div className="flex justify-between items-start mb-3">
                                <div>
                                    <h3 className="font-semibold text-gray-900 dark:text-white">
                                        {draft.template_title}
                                    </h3>
                                    <p className="text-sm text-gray-500 dark:text-gray-400">
                                        {formatDate(draft.created_at)}
                                    </p>
                                </div>
                                <span className="text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 px-2 py-1 rounded">
                                    Draft #{draft.id}
                                </span>
                            </div>

                            {draft.user_query && (
                                <p className="text-sm text-gray-600 dark:text-gray-400 mb-3 italic">
                                    "{draft.user_query}"
                                </p>
                            )}

                            <p className="text-sm text-gray-700 dark:text-gray-300 mb-4 line-clamp-2">
                                {draft.preview}
                            </p>

                            <div className="flex gap-2">
                                <button
                                    onClick={() => handleView(draft.id)}
                                    className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                                >
                                    View Full Draft
                                </button>
                                <button
                                    onClick={() => window.open(`http://localhost:8000/api/drafts/${draft.id}/download`, '_blank')}
                                    className="px-4 py-2 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 
                             rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                                >
                                    Download
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Draft Modal */}
            {selectedDraft && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white dark:bg-gray-800 rounded-xl w-full max-w-4xl max-h-[90vh] overflow-hidden">
                        <div className="flex justify-between items-center p-4 border-b border-gray-200 dark:border-gray-700">
                            <h3 className="font-semibold text-gray-900 dark:text-white">
                                {selectedDraft.template_title}
                            </h3>
                            <button
                                onClick={() => setSelectedDraft(null)}
                                className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
                            >
                                ✕
                            </button>
                        </div>

                        <div className="p-4 overflow-y-auto max-h-[60vh]">
                            <pre className="whitespace-pre-wrap text-sm font-mono text-gray-800 dark:text-gray-200">
                                {selectedDraft.draft_md}
                            </pre>
                        </div>

                        <div className="flex gap-2 p-4 border-t border-gray-200 dark:border-gray-700">
                            <button
                                onClick={() => handleCopy(selectedDraft.draft_md)}
                                className="px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 
                           rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                            >
                                📋 Copy
                            </button>
                            <button
                                onClick={() => handleDownload(selectedDraft)}
                                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                            >
                                📥 Download .md
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
