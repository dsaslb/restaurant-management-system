import * as React from "react";

export interface ProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  value: number;
  className?: string;
}

export function Progress({ value, className, ...props }: ProgressProps) {
  return (
    <div className={`w-full bg-gray-200 rounded-full h-2 ${className ?? ""}`} {...props}>
      <div
        className="bg-blue-500 h-2 rounded-full transition-all"
        style={{ width: `${value}%` }}
      />
    </div>
  );
} 