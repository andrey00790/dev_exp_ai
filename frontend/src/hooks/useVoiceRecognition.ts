import { useState, useEffect, useRef, useCallback } from 'react';

interface UseVoiceRecognitionOptions {
  language?: string;
  continuous?: boolean;
  interimResults?: boolean;
  maxAlternatives?: number;
  onResult?: (transcript: string, confidence: number) => void;
  onError?: (error: string) => void;
  onStart?: () => void;
  onEnd?: () => void;
}

interface VoiceRecognitionState {
  isListening: boolean;
  isSupported: boolean;
  transcript: string;
  confidence: number;
  error: string | null;
  interimTranscript: string;
  finalTranscript: string;
}

interface VoiceRecognitionControls {
  startListening: () => void;
  stopListening: () => void;
  toggleListening: () => void;
  resetTranscript: () => void;
  speakText: (text: string) => void;
  stopSpeaking: () => void;
  isSpeaking: boolean;
}

type UseVoiceRecognitionReturn = [VoiceRecognitionState, VoiceRecognitionControls];

export const useVoiceRecognition = (
  options: UseVoiceRecognitionOptions = {}
): UseVoiceRecognitionReturn => {
  const {
    language = 'en-US',
    continuous = true,
    interimResults = true,
    maxAlternatives = 1,
    onResult,
    onError,
    onStart,
    onEnd
  } = options;

  const [state, setState] = useState<VoiceRecognitionState>({
    isListening: false,
    isSupported: false,
    transcript: '',
    confidence: 0,
    error: null,
    interimTranscript: '',
    finalTranscript: ''
  });

  const [isSpeaking, setIsSpeaking] = useState(false);
  
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Initialize Speech Recognition
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (SpeechRecognition) {
      setState(prev => ({ ...prev, isSupported: true }));
      
      const recognition = new SpeechRecognition();
      recognition.continuous = continuous;
      recognition.interimResults = interimResults;
      recognition.lang = language;
      recognition.maxAlternatives = maxAlternatives;
      
      recognition.onstart = () => {
        setState(prev => ({ 
          ...prev, 
          isListening: true, 
          error: null,
          transcript: '',
          interimTranscript: '',
          finalTranscript: ''
        }));
        onStart?.();
      };
      
      recognition.onresult = (event: SpeechRecognitionEvent) => {
        let finalTranscript = '';
        let interimTranscript = '';
        let lastConfidence = 0;
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const result = event.results[i];
          const transcriptText = result[0].transcript;
          
          if (result.isFinal) {
            finalTranscript += transcriptText;
            lastConfidence = result[0].confidence;
          } else {
            interimTranscript += transcriptText;
          }
        }
        
        const fullTranscript = finalTranscript || interimTranscript;
        
        setState(prev => ({
          ...prev,
          transcript: fullTranscript,
          finalTranscript,
          interimTranscript,
          confidence: lastConfidence
        }));
        
        if (finalTranscript) {
          onResult?.(finalTranscript, lastConfidence);
        }
        
        // Auto-stop after periods of silence
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
        }
        
        timeoutRef.current = setTimeout(() => {
          if (recognitionRef.current && state.isListening) {
            recognitionRef.current.stop();
          }
        }, 5000);
      };
      
      recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
        let errorMessage = 'Speech recognition error';
        
        switch (event.error) {
          case 'no-speech':
            errorMessage = 'No speech detected. Please try again.';
            break;
          case 'audio-capture':
            errorMessage = 'No microphone found. Please check your microphone.';
            break;
          case 'not-allowed':
            errorMessage = 'Microphone permission denied. Please enable microphone access.';
            break;
          case 'network':
            errorMessage = 'Network error. Please check your internet connection.';
            break;
          case 'service-not-allowed':
            errorMessage = 'Speech recognition service not allowed.';
            break;
          case 'bad-grammar':
            errorMessage = 'Grammar error in recognition.';
            break;
          case 'language-not-supported':
            errorMessage = `Language ${language} is not supported.`;
            break;
          default:
            errorMessage = `Speech recognition error: ${event.error}`;
        }
        
        setState(prev => ({ ...prev, error: errorMessage, isListening: false }));
        onError?.(errorMessage);
      };
      
      recognition.onend = () => {
        setState(prev => ({ ...prev, isListening: false }));
        onEnd?.();
        
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
        }
      };
      
      recognitionRef.current = recognition;
    } else {
      setState(prev => ({ 
        ...prev, 
        isSupported: false, 
        error: 'Speech recognition is not supported in this browser.' 
      }));
    }
    
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
    };
  }, [language, continuous, interimResults, maxAlternatives, onResult, onError, onStart, onEnd]);

  const startListening = useCallback(() => {
    if (!state.isSupported || !recognitionRef.current) return;
    
    try {
      recognitionRef.current.start();
    } catch (err) {
      const errorMessage = 'Failed to start speech recognition. Please try again.';
      setState(prev => ({ ...prev, error: errorMessage }));
      onError?.(errorMessage);
    }
  }, [state.isSupported, onError]);

  const stopListening = useCallback(() => {
    if (recognitionRef.current && state.isListening) {
      recognitionRef.current.stop();
    }
  }, [state.isListening]);

  const toggleListening = useCallback(() => {
    if (state.isListening) {
      stopListening();
    } else {
      startListening();
    }
  }, [state.isListening, startListening, stopListening]);

  const resetTranscript = useCallback(() => {
    setState(prev => ({
      ...prev,
      transcript: '',
      finalTranscript: '',
      interimTranscript: '',
      confidence: 0,
      error: null
    }));
  }, []);

  // Text-to-Speech functionality
  const speakText = useCallback((text: string) => {
    if (!text.trim()) return;
    
    // Cancel any ongoing speech
    window.speechSynthesis.cancel();
    
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = language;
    utterance.rate = 0.9;
    utterance.pitch = 1;
    utterance.volume = 0.8;
    
    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);
    
    window.speechSynthesis.speak(utterance);
  }, [language]);

  const stopSpeaking = useCallback(() => {
    window.speechSynthesis.cancel();
    setIsSpeaking(false);
  }, []);

  const controls: VoiceRecognitionControls = {
    startListening,
    stopListening,
    toggleListening,
    resetTranscript,
    speakText,
    stopSpeaking,
    isSpeaking
  };

  return [state, controls];
};

// Utility hook for simple voice commands
export const useVoiceCommands = (
  commands: Record<string, () => void>,
  options: Omit<UseVoiceRecognitionOptions, 'onResult'> = {}
) => {
  const [state, controls] = useVoiceRecognition({
    ...options,
    continuous: false,
    onResult: (transcript) => {
      const command = transcript.toLowerCase().trim();
      
      // Exact match
      if (commands[command]) {
        commands[command]();
        return;
      }
      
      // Fuzzy match
      const commandKeys = Object.keys(commands);
      const matchedCommand = commandKeys.find(key => 
        command.includes(key.toLowerCase()) || 
        key.toLowerCase().includes(command)
      );
      
      if (matchedCommand) {
        commands[matchedCommand]();
      }
    }
  });

  return [state, controls] as const;
};

export default useVoiceRecognition; 