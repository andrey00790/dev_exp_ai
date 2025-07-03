import React, { useState, useEffect } from 'react';
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle 
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { 
  Alert, 
  AlertDescription 
} from '@/components/ui/alert';
import { 
  Loader2, 
  Shield, 
  ExternalLink,
  AlertCircle,
  CheckCircle
} from 'lucide-react';

interface SSOProvider {
  id: number;
  name: string;
  provider_type: string;
  enabled: boolean;
  available: boolean;
  login_url: string;
  display_name?: string;
  icon?: string;
  color?: string;
}

interface SSOLoginProps {
  onSuccess?: (token: string) => void;
  onError?: (error: string) => void;
  className?: string;
}

export const SSOLogin: React.FC<SSOLoginProps> = ({
  onSuccess,
  onError,
  className = ""
}) => {
  const [providers, setProviders] = useState<SSOProvider[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [authenticating, setAuthenticating] = useState<number | null>(null);

  useEffect(() => {
    loadSSOProviders();
  }, []);

  const loadSSOProviders = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/auth/sso/providers');
      
      if (!response.ok) {
        throw new Error('Failed to load SSO providers');
      }
      
      const data = await response.json();
      setProviders(data.filter((p: SSOProvider) => p.enabled && p.available));
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load SSO providers');
      onError?.(err instanceof Error ? err.message : 'SSO loading failed');
    } finally {
      setLoading(false);
    }
  };

  const initiateSSO = async (provider: SSOProvider) => {
    try {
      setAuthenticating(provider.id);
      setError(null);

      const response = await fetch(`/api/v1/auth/sso/login/${provider.id}`);
      
      if (!response.ok) {
        throw new Error('Failed to initiate SSO login');
      }
      
      const data = await response.json();
      
      if (data.type === 'redirect' && data.url) {
        // Redirect to SSO provider
        window.location.href = data.url;
      } else {
        throw new Error('Invalid SSO response');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'SSO login failed');
      onError?.(err instanceof Error ? err.message : 'SSO login failed');
      setAuthenticating(null);
    }
  };

  const getProviderIcon = (provider: SSOProvider) => {
    const iconMap: Record<string, string> = {
      google: '🔍',
      microsoft: '🏢',
      github: '🐙',
      okta: '🔐',
      saml: '🛡️'
    };

    return iconMap[provider.icon || provider.provider_type] || '🔑';
  };

  const getProviderColor = (provider: SSOProvider) => {
    const colorMap: Record<string, string> = {
      google: 'bg-blue-500 hover:bg-blue-600',
      microsoft: 'bg-blue-600 hover:bg-blue-700',
      github: 'bg-gray-800 hover:bg-gray-900',
      okta: 'bg-blue-700 hover:bg-blue-800',
      saml: 'bg-green-600 hover:bg-green-700'
    };

    return colorMap[provider.icon || provider.provider_type] || 'bg-gray-600 hover:bg-gray-700';
  };

  if (loading) {
    return (
      <Card className={`w-full max-w-md mx-auto ${className}`}>
        <CardHeader className="text-center">
          <CardTitle className="flex items-center justify-center gap-2">
            <Shield className="h-5 w-5" />
            Enterprise Login
          </CardTitle>
          <CardDescription>
            Loading authentication providers...
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error && providers.length === 0) {
    return (
      <Card className={`w-full max-w-md mx-auto ${className}`}>
        <CardHeader className="text-center">
          <CardTitle className="flex items-center justify-center gap-2 text-red-600">
            <AlertCircle className="h-5 w-5" />
            SSO Unavailable
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              {error}
            </AlertDescription>
          </Alert>
          <Button 
            onClick={loadSSOProviders}
            variant="outline"
            className="w-full mt-4"
          >
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={`w-full max-w-md mx-auto ${className}`}>
      <CardHeader className="text-center">
        <CardTitle className="flex items-center justify-center gap-2">
          <Shield className="h-5 w-5" />
          Enterprise Login
        </CardTitle>
        <CardDescription>
          Sign in with your organization account
        </CardDescription>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              {error}
            </AlertDescription>
          </Alert>
        )}

        {providers.length === 0 ? (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              No SSO providers are currently available. Please contact your administrator.
            </AlertDescription>
          </Alert>
        ) : (
          <div className="space-y-3">
            {providers.map((provider) => (
              <Button
                key={provider.id}
                onClick={() => initiateSSO(provider)}
                disabled={authenticating !== null}
                className={`w-full h-12 text-white ${getProviderColor(provider)} transition-colors`}
              >
                {authenticating === provider.id ? (
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                ) : (
                  <span className="text-xl mr-3">
                    {getProviderIcon(provider)}
                  </span>
                )}
                <span className="flex-1 text-left">
                  Continue with {provider.display_name || provider.name}
                </span>
                <ExternalLink className="h-4 w-4 ml-2" />
              </Button>
            ))}
          </div>
        )}

        <div className="text-center text-sm text-gray-500 space-y-2">
          <p>
            By signing in, you agree to your organization's security policies.
          </p>
          <div className="flex items-center justify-center gap-1 text-green-600">
            <CheckCircle className="h-3 w-3" />
            <span className="text-xs">Secure enterprise authentication</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default SSOLogin; 