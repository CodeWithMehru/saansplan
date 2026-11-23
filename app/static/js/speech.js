/**
 * Speech capabilities: Read aloud (speechSynthesis) and voice input (SpeechRecognition) with graceful fallbacks.
 */

import { announce } from './a11y/focus.js';

export function isSpeechSynthesisSupported() {
  return typeof window !== 'undefined' && 'speechSynthesis' in window && 'SpeechSynthesisUtterance' in window;
}

export function isSpeechRecognitionSupported() {
  return typeof window !== 'undefined' && ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window);
}

export function speakText(text, lang = 'en') {
  if (!isSpeechSynthesisSupported()) {
    announce('Text-to-speech is not supported in your browser.');
    return;
  }
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = lang === 'hi' ? 'hi-IN' : 'en-IN';
  utterance.rate = 0.95;
  window.speechSynthesis.speak(utterance);
  announce('Reading plan summary aloud.');
}

export function startVoiceRecognition({ onResult, onError, onStart, onEnd, lang = 'en' }) {
  if (!isSpeechRecognitionSupported()) {
    if (onError) onError('Voice input is not supported in this browser.');
    return null;
  }

  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
  const recognition = new SpeechRec();
  recognition.lang = lang === 'hi' ? 'hi-IN' : 'en-IN';
  recognition.continuous = false;
  recognition.interimResults = false;

  recognition.onstart = () => {
    if (onStart) onStart();
    announce('Microphone listening, speak your daily routine.');
  };

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    if (onResult) onResult(transcript);
    announce('Voice routine captured.');
  };

  recognition.onerror = (event) => {
    if (onError) onError(event.error);
  };

  recognition.onend = () => {
    if (onEnd) onEnd();
  };

  recognition.start();
  return recognition;
}
