import type { Conversation, Evidence, Message } from './types';

export const statusOf = (row: Conversation) => !row.evaluation ? 'not_evaluated' : row.evaluation.state === 'succeeded' ? row.evaluation.completeness : row.evaluation.state;
export const label = (value: string) => value.replaceAll('_', ' ');
export const points = (value: string | number | null | undefined) => value == null ? '—' : Number(value).toLocaleString('en', { maximumFractionDigits: 4 });

export function evidenceMessages(messages: Message[], evidence: Evidence): Message[] {
  const start = messages.findIndex(m => m.id === evidence.start_message_id);
  const end = messages.findIndex(m => m.id === evidence.end_message_id);
  return start < 0 || end < start ? [] : messages.slice(start, end + 1);
}

export function answerLabel(value: boolean | number | null, disposition: string) {
  if (disposition === 'not_applicable') return 'N/A';
  if (disposition === 'needs_review') return 'Needs review';
  return typeof value === 'boolean' ? value ? 'Yes' : 'No' : String(value);
}
