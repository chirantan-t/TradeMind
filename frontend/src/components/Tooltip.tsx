import { useState } from 'react';
import { HelpCircle } from 'lucide-react';

interface Props {
  text: string;
  children: React.ReactNode;
}

export function Tooltip({ text, children }: Props) {
  const [show, setShow] = useState(false);

  return (
    <div 
      className="relative flex items-center gap-1 group"
      onMouseEnter={() => setShow(true)}
      onMouseLeave={() => setShow(false)}
    >
      {children}
      <HelpCircle size={12} className="text-text-muted cursor-help" />
      
      {show && (
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 p-2 bg-bg-card border border-border rounded-md shadow-lg z-50 text-[11px] text-text-secondary leading-tight normal-case font-sans tracking-normal">
          {text}
        </div>
      )}
    </div>
  );
}
