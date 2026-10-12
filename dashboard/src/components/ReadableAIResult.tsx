import { useEffect, useRef } from 'react';
import { renderAnswer } from '../native-ai/readable-report.mjs';
import './ReadableAIResult.css';

/** Displays the same structured view for immediate and saved AI answers. */
export default function ReadableAIResult({ value }: { value: unknown }) {
  const output = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const text = typeof value === 'string' ? value : JSON.stringify(value);
    output.current?.replaceChildren(renderAnswer(text ?? ''));
  }, [value]);
  return <div ref={output} className="readable-ai-result" aria-label="AI result" />;
}
