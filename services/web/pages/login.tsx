import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '@/hooks/useAuth';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { GoogleIcon, FacebookIcon } from '@/components/icons';
import { toast } from '@/components/ui/use-toast';

export default function LoginPage() {
  const [isLoading, setIsLoading] = useState(false);
  const { isAuthenticated, login, error } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isAuthenticated) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, router]);

  useEffect(() => {
    if (error) {
      toast({
        variant: 'destructive',
        title: 'Login Failed',
        description: error,
      });
    }
  }, [error]);

  const handleGoogleLogin = async () => {
    try {
      setIsLoading(true);
      
      // Open Google OAuth popup
      const googleAuthUrl = `https://accounts.google.com/o/oauth2/v2/auth?` +
        `client_id=${process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID}&` +
        `redirect_uri=${encodeURIComponent(process.env.NEXT_PUBLIC_GOOGLE_REDIRECT_URI || 'http://localhost:3000/auth/callback/google')}&` +
        `response_type=token&` +
        `scope=openid%20email%20profile&` +
        `state=google`;
      
      // For demo purposes, we'll simulate the OAuth flow
      // In production, you would open a popup and handle the callback
      toast({
        title: 'Google Login',
        description: 'Opening Google OAuth popup...',
      });
      
      // This is a placeholder - in production, you would:
      // 1. Open a popup to the Google OAuth URL
      // 2. Handle the callback in a separate page
      // 3. Extract the access token from the URL hash
      // 4. Call the login function with the token
      
    } catch (error) {
      console.error('Google login failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFacebookLogin = async () => {
    try {
      setIsLoading(true);
      
      // Open Facebook OAuth popup
      const facebookAuthUrl = `https://www.facebook.com/v18.0/dialog/oauth?` +
        `client_id=${process.env.NEXT_PUBLIC_FACEBOOK_CLIENT_ID}&` +
        `redirect_uri=${encodeURIComponent(process.env.NEXT_PUBLIC_FACEBOOK_REDIRECT_URI || 'http://localhost:3000/auth/callback/facebook')}&` +
        `response_type=token&` +
        `scope=email,public_profile&` +
        `state=facebook`;
      
      // For demo purposes, we'll simulate the OAuth flow
      toast({
        title: 'Facebook Login',
        description: 'Opening Facebook OAuth popup...',
      });
      
      // This is a placeholder - in production, you would:
      // 1. Open a popup to the Facebook OAuth URL
      // 2. Handle the callback in a separate page
      // 3. Extract the access token from the URL hash
      // 4. Call the login function with the token
      
    } catch (error) {
      console.error('Facebook login failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl">Welcome to Roster</CardTitle>
          <CardDescription>
            Sign in to manage your team shifts
          </CardDescription>
        </CardHeader>
        
        <CardContent className="space-y-4">
          <Button
            variant="outline"
            className="w-full"
            onClick={handleGoogleLogin}
            disabled={isLoading}
          >
            <GoogleIcon className="mr-2 h-4 w-4" />
            Continue with Google
          </Button>
          
          <Button
            variant="outline"
            className="w-full"
            onClick={handleFacebookLogin}
            disabled={isLoading}
          >
            <FacebookIcon className="mr-2 h-4 w-4" />
            Continue with Facebook
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
