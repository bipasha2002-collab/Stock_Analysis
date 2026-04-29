'use client';

interface ErrorMessageProps {
  message: string;
  onRetry?: () => void;
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({ message, onRetry }) => {
  return (
    <div className="max-w-md mx-auto">
      <div className="bg-[rgb(var(--charcoal))] border border-white/10 rounded-xl p-6 text-center">
        <div className="text-[rgb(var(--soft-red))] mb-4">
          <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h3 className="text-lg font-semibold text-white mb-2">Analysis Failed</h3>
        <p className="text-[rgb(var(--blue-gray))] mb-4">{message}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="px-4 py-2 bg-white/5 text-white rounded-lg hover:bg-white/10 active:bg-white/15 transition-colors border border-white/10"
          >
            Try Again
          </button>
        )}
      </div>
    </div>
  );
};
