// Auctor Systems — Workflow Types & State Constants
// Strict compliance with Palette 4 Design Tokens

export const AGENT_STATES = {
  IDLE: 'idle',
  THINKING: 'thinking',
  WORKING: 'working',
  COMMUNICATING: 'communicating',
  COMPLETED: 'completed',
  ERROR: 'error',
};

export const EVENT_TYPES = {
  THINKING: 'thinking',
  WORKING: 'working',
  HANDOFF: 'handoff',
  DIALOGUE: 'dialogue',
  REVIEW: 'review',
  QUESTION: 'question',
  ANSWER: 'answer',
  COMPLETED: 'completed',
  ERROR: 'error',
};

export const ORCHESTRATOR_STATES = {
  IDLE: 'idle',
  ORCHESTRATING: 'orchestrating',
  WORKING: 'working',
  WAITING_USER: 'waiting_user',
  COMPLETED: 'completed',
  ERROR: 'error',
};

export const AGENT_ORDER = [
  'planning',
  'requirements',
  'design',
  'development',
  'testing',
  'documentation',
  'deployment',
  'marketing',
];
