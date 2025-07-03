import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Volume2, VolumeX } from 'lucide-react';

interface VoiceInputProps {
  onVoiceText: (text: string) => void;
  onVoiceStart?: () => void;
  onVoiceEnd?: () => void;
  placeholder?: string;
  language?: string;
  continuous?: boolean;
  disabled?: boolean;
  className?: string;
}

interface SpeechRecognitionResult {
  transcript: string;
  confidence: number;
  isFinal: boolean;
}

declare global {
  interface Window {
    SpeechRecognition: typeof SpeechRecognition;
    webkitSpeechRecognition: typeof SpeechRecognition;
  }
}

const VoiceInput: React.FC<VoiceInputProps> = ({
  onVoiceText,
  onVoiceStart,
  onVoiceEnd,
  placeholder = "Click microphone to start speaking...",
  language = 'en-US',
  continuous = true,
  disabled = false,
  className = ''
}) => {
  const [isListening, setIsListening] = useState(false);
  const [isSupported, setIsSupported] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [confidence, setConfidence] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [isSpeaking, setIsSpeaking] = useState(false);
  
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    // Check if Speech Recognition is supported
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (SpeechRecognition) {
      setIsSupported(true);
      
      const recognition = new SpeechRecognition();
      recognition.continuous = continuous;
      recognition.interimResults = true;
      recognition.lang = language;
      recognition.maxAlternatives = 1;
      
      recognition.onstart = () => {
        setIsListening(true);
        setError(null);
        onVoiceStart?.();
      };
      
      recognition.onresult = (event: SpeechRecognitionEvent) => {
        let finalTranscript = '';
        let interimTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const result = event.results[i];
          const transcriptText = result[0].transcript;
          
          if (result.isFinal) {
            finalTranscript += transcriptText;
            setConfidence(result[0].confidence);
          } else {
            interimTranscript += transcriptText;
          }
        }
        
        const fullTranscript = finalTranscript || interimTranscript;
        setTranscript(fullTranscript);
        
        if (finalTranscript) {
          onVoiceText(finalTranscript);
          
          if (!continuous) {
            stopListening();
          }
        }
        
        // Auto-stop after 5 seconds of silence
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
        }
        
        timeoutRef.current = setTimeout(() => {
          if (isListening) {
            stopListening();
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
          default:
            errorMessage = `Speech recognition error: ${event.error}`;
        }
        
        setError(errorMessage);
        setIsListening(false);
      };
      
      recognition.onend = () => {
        setIsListening(false);
        onVoiceEnd?.();
        
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
        }
      };
      
      recognitionRef.current = recognition;
    } else {
      setIsSupported(false);
      setError('Speech recognition is not supported in this browser. Please use Chrome, Edge, or Safari.');
    }
    
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
    };
  }, [language, continuous, onVoiceStart, onVoiceEnd, onVoiceText, isListening]);

  const startListening = () => {
    if (!isSupported || !recognitionRef.current || disabled) return;
    
    setTranscript('');
    setError(null);
    
    try {
      recognitionRef.current.start();
    } catch (err) {
      setError('Failed to start speech recognition. Please try again.');
    }
  };

  const stopListening = () => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop();
    }
  };

  const toggleListening = () => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  };

  // Text-to-Speech functionality
  const speakText = (text: string) => {
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
  };

  const stopSpeaking = () => {
    window.speechSynthesis.cancel();
    setIsSpeaking(false);
  };

  const toggleSpeaking = () => {
    if (isSpeaking) {
      stopSpeaking();
    } else if (transcript) {
      speakText(transcript);
    }
  };

  if (!isSupported) {
    return (
      <div className={`voice-input-container ${className}`}>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <MicOff className="w-5 h-5 text-red-500 mr-2" />
            <span className="text-red-700 text-sm">
              Speech recognition is not supported in this browser. Please use Chrome, Edge, or Safari.
            </span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`voice-input-container ${className}`}>
      <div className="flex items-center space-x-3">
        {/* Voice Input Button */}
        <button
          onClick={toggleListening}
          disabled={disabled}
          className={`
            relative flex items-center justify-center w-12 h-12 rounded-full border-2 transition-all duration-200
            ${isListening 
              ? 'bg-red-500 border-red-500 text-white shadow-lg' 
              : 'bg-white border-gray-300 text-gray-600 hover:border-blue-500 hover:text-blue-500'
            }
            ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
          `}
          title={isListening ? 'Stop recording' : 'Start voice input'}
        >
          {isListening ? (
            <MicOff className="w-5 h-5" />
          ) : (
            <Mic className="w-5 h-5" />
          )}
          
          {/* Recording indicator */}
          {isListening && (
            <div className="absolute -top-1 -right-1 w-3 h-3 bg-red-400 rounded-full animate-pulse" />
          )}
        </button>

        {/* Text-to-Speech Button */}
        {transcript && (
          <button
            onClick={toggleSpeaking}
            className={`
              flex items-center justify-center w-10 h-10 rounded-full border transition-all duration-200
              ${isSpeaking 
                ? 'bg-blue-500 border-blue-500 text-white' 
                : 'bg-white border-gray-300 text-gray-600 hover:border-blue-500 hover:text-blue-500'
              }
            `}
            title={isSpeaking ? 'Stop speaking' : 'Read transcript aloud'}
          >
            {isSpeaking ? (
              <VolumeX className="w-4 h-4" />
            ) : (
              <Volume2 className="w-4 h-4" />
            )}
          </button>
        )}

        {/* Status Text */}
        <div className="flex-1 min-w-0">
          {isListening && (
            <div className="text-sm text-blue-600 font-medium">
              🎤 Listening... {transcript && `"${transcript}"`}
            </div>
          )}
          
          {!isListening && transcript && (
            <div className="text-sm text-gray-600">
              Last: "{transcript}" 
              {confidence > 0 && (
                <span className="ml-2 text-xs text-gray-400">
                  ({Math.round(confidence * 100)}% confidence)
                </span>
              )}
            </div>
          )}
          
          {!isListening && !transcript && (
            <div className="text-sm text-gray-400">
              {placeholder}
            </div>
          )}
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mt-3 bg-red-50 border border-red-200 rounded-lg p-3">
          <div className="flex items-center">
            <MicOff className="w-4 h-4 text-red-500 mr-2 flex-shrink-0" />
            <span className="text-red-700 text-sm">{error}</span>
          </div>
        </div>
      )}

      {/* Language and Settings Info */}
      <div className="mt-2 text-xs text-gray-400">
        Language: {language} • {continuous ? 'Continuous' : 'Single command'} mode
      </div>
    </div>
  );
};

export default VoiceInput; 