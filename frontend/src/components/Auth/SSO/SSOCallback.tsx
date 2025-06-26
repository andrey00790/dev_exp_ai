import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle 
} from '@/components/ui/card';
import { 
  Alert, 
  AlertDescription 
} from '@/components/ui/alert';
import { 
  Loader2, 
  CheckCircle, 
  AlertCircle,
  Shield
} from 'lucide-react';
import { Button } from '@/components/ui/button';

interface SSOCallbackProps {
  onSuccess?: (token: string) => void;
  onError?: (error: string) => void;
}

export const SSOCallback: React.FC<SSOCallbackProps> = ({
  onSuccess,
  onError
}) => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState<'processing' | 'success' | 'error'>('processing');
  const [message, setMessage] = useState('Processing authentication...');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    handleCallback();
  }, []);

  const handleCallback = async () => {
    try {
      // Check for OAuth token in URL params
      const token = searchParams.get('token');
      const error = searchParams.get('error');
      const errorDescription = searchParams.get('error_description');

      if (error) {
        throw new Error(errorDescription || error);
      }

      if (token) {
        // Token received directly (OAuth flow)
        setStatus('success');
        setMessage('Authentication successful! Redirecting...');
        
        // Store token
        localStorage.setItem('access_token', token);
        
        // Call success callback
        onSuccess?.(token);
        
        // Redirect to dashboard after short delay
        setTimeout(() => {
          navigate('/dashboard');
        }, 2000);
        
        return;
      }

      // Check for SAML response or other auth flows
      const samlResponse = searchParams.get('SAMLResponse');
      if (samlResponse) {
        setMessage('Processing SAML response...');
        // SAML responses are typically handled by form submission
        // This might not be reached in normal SAML flow
      }

      // If no token and no error, something went wrong
      if (!token && !samlResponse) {
        throw new Error('No authentication token received');
      }

    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Authentication failed';
      setStatus('error');
      setError(errorMsg);
      setMessage('Authentication failed');
      onError?.(errorMsg);
    }
  };

  const handleRetry = () => {
    navigate('/login');
  };

  const handleGoToDashboard = () => {
    navigate('/dashboard');
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="flex items-center justify-center gap-2">
            <Shield className="h-5 w-5" />
            Enterprise Authentication
          </CardTitle>
          <CardDescription>
            {status === 'processing' && 'Processing your authentication...'}
            {status === 'success' && 'Authentication completed successfully'}
            {status === 'error' && 'Authentication encountered an error'}
          </CardDescription>
        </CardHeader>
        
        <CardContent className="space-y-6">
          {status === 'processing' && (
            <div className="flex flex-col items-center space-y-4">
              <Loader2 className="h-12 w-12 animate-spin text-blue-500" />
              <p className="text-center text-sm text-gray-600">
                {message}
              </p>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-blue-500 h-2 rounded-full animate-pulse w-3/4"></div>
              </div>
            </div>
          )}

          {status === 'success' && (
            <div className="flex flex-col items-center space-y-4">
              <div className="flex items-center justify-center w-16 h-16 bg-green-100 rounded-full">
                <CheckCircle className="h-8 w-8 text-green-600" />
              </div>
              <div className="text-center">
                <h3 className="text-lg font-semibold text-green-800">
                  Welcome back!
                </h3>
                <p className="text-sm text-gray-600 mt-1">
                  {message}
                </p>
              </div>
              <Button 
                onClick={handleGoToDashboard}
                className="w-full"
              >
                Go to Dashboard
              </Button>
            </div>
          )}

          {status === 'error' && (
            <div className="space-y-4">
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  {error}
                </AlertDescription>
              </Alert>
              
              <div className="space-y-2">
                <Button 
                  onClick={handleRetry}
                  variant="default"
                  className="w-full"
                >
                  Try Again
                </Button>
                <Button 
                  onClick={() => navigate('/login')}
                  variant="outline"
                  className="w-full"
                >
                  Back to Login
                </Button>
              </div>
              
              <div className="text-center">
                <p className="text-xs text-gray-500">
                  If you continue to experience issues, please contact your system administrator.
                </p>
              </div>
            </div>
          )}

          {/* Debug information (only in development) */}
          {process.env.NODE_ENV === 'development' && (
            <details className="mt-4">
              <summary className="text-xs text-gray-400 cursor-pointer">
                Debug Information
              </summary>
              <div className="mt-2 p-2 bg-gray-100 rounded text-xs">
                <pre className="whitespace-pre-wrap">
                  {JSON.stringify(Object.fromEntries(searchParams), null, 2)}
                </pre>
              </div>
            </details>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default SSOCallback; 