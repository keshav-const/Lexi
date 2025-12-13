/* CREATED BY UOIONHHC */
'use client';

import { useState, useRef, useEffect } from 'react';
import { matchTemplate, getQuestions, generateDraft, getTemplate } from '@/lib/api';

interface Message {
    id: string;
    type: 'user' | 'assistant' | 'system';
    content: string;
    templateMatch?: {
        template_id: string;
        title: string;
        score: number;
        reason: string;
        doc_type?: string;
        similarity_tags: string[];
    };
    alternatives?: Array<{
        template_id: string;
        title: string;
        score: number;
        reason: string;
    }>;
    questions?: Array<{
        key: string;
        question: string;
        hint?: string;
        example?: string;
        required: boolean;
    }>;
    draft?: {
        draft_id: number;
        draft_md: string;
        template_title: string;
    };
}

export default function ChatInterface() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [currentTemplate, setCurrentTemplate] = useState<string | null>(null);
    const [currentAnswers, setCurrentAnswers] = useState<Record<string, string>>({});
    const [pendingQuestions, setPendingQuestions] = useState<Message['questions']>(null);
    const [userQuery, setUserQuery] = useState('');

    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const addMessage = (message: Omit<Message, 'id'>) => {
        const newMessage = {
            ...message,
            id: Date.now().toString(),
        };
        setMessages(prev => [...prev, newMessage]);
        return newMessage.id;
    };

    const handleSend = async () => {
        if (!input.trim() || isLoading) return;

        const userMessage = input.trim();
        setInput('');
        setUserQuery(userMessage);

        // Add user message
        addMessage({ type: 'user', content: userMessage });

        // Check for slash commands
        if (userMessage.startsWith('/vars') && currentTemplate) {
            try {
                const template = await getTemplate(currentTemplate);
                const varsText = template.variables.map(v =>
                    `• **${v.label}** (${v.key}): ${currentAnswers[v.key] || '_not filled_'}`
                ).join('\n');
                addMessage({ type: 'assistant', content: `## Current Variables\n\n${varsText}` });
            } catch (error) {
                addMessage({ type: 'system', content: 'Failed to fetch variables' });
            }
            return;
        }

        setIsLoading(true);

        try {
            // Match template
            const matchResult = await matchTemplate(userMessage);

            if (!matchResult.best_match) {
                addMessage({
                    type: 'assistant',
                    content: '❌ **No matching template found.**\n\nI couldn\'t find a suitable template in the database for your request. Please try:\n- Uploading a similar document first\n- Being more specific about the document type\n- Checking the Templates page for available options',
                });
                setIsLoading(false);
                return;
            }

            // Store prefilled variables
            setCurrentAnswers(matchResult.prefilled_variables || {});
            setCurrentTemplate(matchResult.best_match.template_id);

            // Show template match
            addMessage({
                type: 'assistant',
                content: `✅ **Found a matching template!**\n\n**Match Score:** ${Math.round(matchResult.best_match.score * 100)}%\n\n**Reason:** ${matchResult.best_match.reason}`,
                templateMatch: matchResult.best_match,
                alternatives: matchResult.alternatives,
            });

            // Get questions for missing variables
            if (matchResult.missing_variables.length > 0) {
                const questions = await getQuestions(
                    matchResult.best_match.template_id,
                    matchResult.missing_variables
                );

                if (questions.length > 0) {
                    setPendingQuestions(questions);
                    addMessage({
                        type: 'assistant',
                        content: `I need a few more details to complete your document. Please answer the following:`,
                        questions: questions,
                    });
                } else {
                    // No questions needed, generate draft immediately
                    await handleGenerateDraft(matchResult.best_match.template_id, matchResult.prefilled_variables || {});
                }
            } else {
                // All variables prefilled, generate draft
                await handleGenerateDraft(matchResult.best_match.template_id, matchResult.prefilled_variables || {});
            }
        } catch (error) {
            addMessage({
                type: 'system',
                content: `Error: ${error instanceof Error ? error.message : 'Something went wrong'}`,
            });
        }

        setIsLoading(false);
    };

    const handleAnswerSubmit = async (answers: Record<string, string>) => {
        // Merge with existing answers
        const allAnswers = { ...currentAnswers, ...answers };
        setCurrentAnswers(allAnswers);
        setPendingQuestions(null);

        // Show user's answers
        const answersText = Object.entries(answers)
            .map(([key, value]) => `**${key}:** ${value}`)
            .join('\n');
        addMessage({ type: 'user', content: answersText });

        // Generate draft
        if (currentTemplate) {
            setIsLoading(true);
            await handleGenerateDraft(currentTemplate, allAnswers);
            setIsLoading(false);
        }
    };

    const handleGenerateDraft = async (templateId: string, answers: Record<string, string>) => {
        try {
            const draft = await generateDraft(templateId, answers, userQuery);

            addMessage({
                type: 'assistant',
                content: `📄 **Your draft is ready!**`,
                draft: draft,
            });
        } catch (error) {
            addMessage({
                type: 'system',
                content: `Failed to generate draft: ${error instanceof Error ? error.message : 'Unknown error'}`,
            });
        }
    };

    const handleUseTemplate = async (templateId: string) => {
        setCurrentTemplate(templateId);
        // Trigger question generation for this template
        try {
            const template = await getTemplate(templateId);
            const questions = await getQuestions(templateId, template.variables.map(v => v.key));

            if (questions.length > 0) {
                setPendingQuestions(questions);
                addMessage({
                    type: 'assistant',
                    content: `Great choice! Please provide the following information:`,
                    questions: questions,
                });
            }
        } catch (error) {
            addMessage({
                type: 'system',
                content: 'Failed to load template questions',
            });
        }
    };

    return (
        <div className="flex flex-col h-full bg-gray-50 dark:bg-gray-900 rounded-xl overflow-hidden">
            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.length === 0 && (
                    <div className="text-center py-12 text-gray-500 dark:text-gray-400">
                        <div className="text-6xl mb-4">💬</div>
                        <h3 className="text-xl font-semibold mb-2">Start a conversation</h3>
                        <p>Tell me what document you'd like to draft, for example:</p>
                        <p className="text-blue-500 mt-2">"Draft a notice to insurer for a car accident"</p>
                    </div>
                )}

                {messages.map((message) => (
                    <div
                        key={message.id}
                        className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                        <div
                            className={`max-w-[80%] rounded-xl p-4 ${message.type === 'user'
                                    ? 'bg-blue-600 text-white'
                                    : message.type === 'system'
                                        ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800'
                                        : 'bg-white dark:bg-gray-800 text-gray-900 dark:text-white shadow-md'
                                }`}
                        >
                            <div className="whitespace-pre-wrap">{message.content}</div>

                            {/* Template Match Card */}
                            {message.templateMatch && (
                                <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/30 rounded-lg border border-blue-200 dark:border-blue-700">
                                    <div className="flex items-center justify-between mb-2">
                                        <h4 className="font-semibold text-blue-700 dark:text-blue-300">
                                            {message.templateMatch.title}
                                        </h4>
                                        <span className="text-xs bg-blue-200 dark:bg-blue-800 text-blue-800 dark:text-blue-200 px-2 py-1 rounded">
                                            {message.templateMatch.doc_type}
                                        </span>
                                    </div>
                                    <div className="flex gap-2 mb-3 flex-wrap">
                                        {message.templateMatch.similarity_tags.map((tag, i) => (
                                            <span key={i} className="text-xs bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300 px-2 py-0.5 rounded">
                                                {tag}
                                            </span>
                                        ))}
                                    </div>
                                    <button
                                        onClick={() => handleUseTemplate(message.templateMatch!.template_id)}
                                        className="w-full py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                                    >
                                        Use This Template
                                    </button>

                                    {message.alternatives && message.alternatives.length > 0 && (
                                        <details className="mt-3">
                                            <summary className="cursor-pointer text-sm text-gray-600 dark:text-gray-400">
                                                See {message.alternatives.length} alternatives
                                            </summary>
                                            <div className="mt-2 space-y-2">
                                                {message.alternatives.map((alt, i) => (
                                                    <button
                                                        key={i}
                                                        onClick={() => handleUseTemplate(alt.template_id)}
                                                        className="w-full text-left p-2 bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                                                    >
                                                        <div className="font-medium text-sm">{alt.title}</div>
                                                        <div className="text-xs text-gray-500">{Math.round(alt.score * 100)}% match</div>
                                                    </button>
                                                ))}
                                            </div>
                                        </details>
                                    )}
                                </div>
                            )}

                            {/* Questions Form */}
                            {message.questions && message.questions.length > 0 && (
                                <QuestionForm
                                    questions={message.questions}
                                    onSubmit={handleAnswerSubmit}
                                />
                            )}

                            {/* Draft Output */}
                            {message.draft && (
                                <DraftOutput draft={message.draft} />
                            )}
                        </div>
                    </div>
                ))}

                {isLoading && (
                    <div className="flex justify-start">
                        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-md">
                            <div className="flex items-center gap-2">
                                <span className="animate-spin w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full"></span>
                                <span className="text-gray-600 dark:text-gray-300">Thinking...</span>
                            </div>
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="p-4 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
                <div className="flex gap-2">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                        placeholder='Try: "Draft a notice to insurer" or type /vars to see variables'
                        disabled={isLoading}
                        className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg
                       bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                       focus:ring-2 focus:ring-blue-500 focus:border-transparent
                       disabled:opacity-50"
                    />
                    <button
                        onClick={handleSend}
                        disabled={isLoading || !input.trim()}
                        className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 
                       transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        Send
                    </button>
                </div>
            </div>
        </div>
    );
}

// Question Form Component
function QuestionForm({ questions, onSubmit }: {
    questions: Array<{
        key: string;
        question: string;
        hint?: string;
        example?: string;
        required: boolean;
    }>;
    onSubmit: (answers: Record<string, string>) => void;
}) {
    const [answers, setAnswers] = useState<Record<string, string>>({});

    const handleSubmit = () => {
        // Check required fields
        const missing = questions.filter(q => q.required && !answers[q.key]?.trim());
        if (missing.length > 0) {
            alert(`Please fill in required fields: ${missing.map(m => m.key).join(', ')}`);
            return;
        }
        onSubmit(answers);
    };

    return (
        <div className="mt-4 space-y-4">
            {questions.map((q) => (
                <div key={q.key} className="space-y-1">
                    <label className="block text-sm font-medium">
                        {q.question}
                        {q.required && <span className="text-red-500 ml-1">*</span>}
                    </label>
                    <input
                        type="text"
                        placeholder={q.example || q.hint}
                        value={answers[q.key] || ''}
                        onChange={(e) => setAnswers(prev => ({ ...prev, [q.key]: e.target.value }))}
                        className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded
                       bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    />
                    {q.hint && <p className="text-xs text-gray-500">{q.hint}</p>}
                </div>
            ))}
            <button
                onClick={handleSubmit}
                className="w-full py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            >
                Generate Draft
            </button>
        </div>
    );
}

// Draft Output Component  
function DraftOutput({ draft }: {
    draft: {
        draft_id: number;
        draft_md: string;
        template_title: string;
    };
}) {
    const [copied, setCopied] = useState(false);

    const handleCopy = () => {
        navigator.clipboard.writeText(draft.draft_md);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const handleDownload = () => {
        const blob = new Blob([draft.draft_md], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${draft.template_title.toLowerCase().replace(/\s+/g, '_')}_draft.md`;
        a.click();
        URL.revokeObjectURL(url);
    };

    return (
        <div className="mt-4 space-y-3">
            <div className="flex gap-2">
                <button
                    onClick={handleCopy}
                    className="flex-1 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 
                     rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors text-sm"
                >
                    {copied ? '✓ Copied!' : '📋 Copy'}
                </button>
                <button
                    onClick={handleDownload}
                    className="flex-1 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 
                     rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors text-sm"
                >
                    📥 Download .md
                </button>
            </div>

            <details className="bg-gray-50 dark:bg-gray-900 rounded-lg">
                <summary className="cursor-pointer p-3 font-medium text-sm">
                    📄 Preview Draft
                </summary>
                <div className="p-4 border-t border-gray-200 dark:border-gray-700">
                    <pre className="whitespace-pre-wrap text-sm font-mono text-gray-800 dark:text-gray-200 max-h-96 overflow-y-auto">
                        {draft.draft_md}
                    </pre>
                </div>
            </details>
        </div>
    );
}
