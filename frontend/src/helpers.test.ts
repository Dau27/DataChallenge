import { describe, expect, it } from 'vitest';
import { answerLabel, evidenceMessages, statusOf } from './helpers';
import type { Conversation, Message } from './types';

describe('source evidence navigation', () => {
  const messages: Message[] = [
    { id: 'm0001', timestamp: '00:00', speaker: 'bot', text: 'SYNTHETIC BOT: hello' },
    { id: 'm0002', timestamp: '00:02', speaker: 'operator', text: 'SYNTHETIC OPERATOR: Қайырлы күн!' },
    { id: 'm0003', timestamp: '00:03', speaker: 'client', text: '<script>SYNTHETIC UNTRUSTED</script>' },
  ];
  it('returns exactly the stored inclusive range without model-written excerpts', () => {
    expect(evidenceMessages(messages, { kind: 'context', start_message_id: 'm0002', end_message_id: 'm0003' })).toEqual(messages.slice(1));
  });
  it('does not navigate fabricated or reversed IDs', () => {
    expect(evidenceMessages(messages, { kind: 'support', start_message_id: 'missing', end_message_id: 'm0003' })).toEqual([]);
    expect(evidenceMessages(messages, { kind: 'support', start_message_id: 'm0003', end_message_id: 'm0001' })).toEqual([]);
  });
});

describe('truthful assessment states', () => {
  it('keeps incomplete, review and execution states separate', () => {
    expect(statusOf({ evaluation: null } as Conversation)).toBe('not_evaluated');
    expect(statusOf({ evaluation: { state: 'succeeded', completeness: 'needs_review' } } as Conversation)).toBe('needs_review');
    expect(statusOf({ evaluation: { state: 'failed', completeness: 'incomplete' } } as Conversation)).toBe('failed');
  });
  it('does not render unresolved or N/A as zero', () => {
    expect(answerLabel(null, 'needs_review')).toBe('Needs review');
    expect(answerLabel(null, 'not_applicable')).toBe('N/A');
    expect(answerLabel(0, 'assessed')).toBe('0');
    expect(answerLabel(false, 'assessed')).toBe('No');
  });
});
