'use client';

export const LoadingSpinner: React.FC = () => {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      <div className="w-12 h-12 border-4 border-[rgb(var(--sage))] border-t-transparent rounded-full animate-spin mb-4"></div>
      <p className="text-[rgb(var(--blue-gray))]">Analyzing stock data...</p>
    </div>
  );
};
