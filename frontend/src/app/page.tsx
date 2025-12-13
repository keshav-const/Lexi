/* CREATED BY UOIONHHC */
import ChatInterface from '@/components/ChatInterface';

export default function Home() {
  return (
    <div className="h-[calc(100vh-8rem)]">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          Document Drafting Assistant
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Tell me what document you need, and I'll help you create it from our templates.
        </p>
      </div>

      <ChatInterface />
    </div>
  );
}
