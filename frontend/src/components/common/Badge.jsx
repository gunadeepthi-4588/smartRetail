import React from 'react';

export default function Badge({ status, text }) {
  const normalized = (status || '').toLowerCase().replace(/\s+/g, '-');
  const className = `badge badge-${normalized}`;
  return <span className={className}>{text || status}</span>;
}
