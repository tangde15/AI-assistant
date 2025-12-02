import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';

interface Props { content: string; }

const MarkdownMessage: React.FC<Props> = ({ content }) => {
  return (
    <div className="markdown-content">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={{
          code({ inline, className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || '');
            if (!inline && match) {
              return (
                <pre className={className + ' relative'}>
                  <div style={{position:'absolute',right:8,top:6,fontSize:12,opacity:.6}}>{match[1]}</div>
                  <code {...props}>{children}</code>
                </pre>
              );
            }
            return <code className="bg-gray-700 px-1 py-0.5 rounded text-sm" {...props}>{children}</code>;
          },
          a({ href, children, ...props }) {
            return <a href={href} target="_blank" rel="noopener" {...props}>{children}</a>;
          },
          table({ children, ...props }) {
            return <div style={{overflowX:'auto'}}><table {...props}>{children}</table></div>;
          }
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};

export default MarkdownMessage;
