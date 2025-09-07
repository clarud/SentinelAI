import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Shield, Eye, Chrome } from 'lucide-react';
import { apiClient } from '@/lib/api';
import sentinelLogo from '@/assets/sentinel-logo.png';

export default function Login() {
  const handleGmailConnect = () => {
    apiClient.connectGmail();
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-subtle p-4">
      <Card className="w-full max-w-md shadow-strong">
        <CardHeader className="text-center space-y-6 pt-8">
          {/* Logo and Branding */}
          <div className="flex flex-col items-center space-y-4">
            <div className="relative">
              <img 
                src={sentinelLogo} 
                alt="SentinelAI Logo" 
                className="w-20 h-20 animate-glow"
              />
            </div>
            
            <div className="space-y-2">
              <h1 className="text-3xl font-bold bg-gradient-accent bg-clip-text text-transparent">
                SentinelAI
              </h1>
              <p className="text-muted-foreground text-sm font-medium">
                Always Watching, Always Protecting
              </p>
            </div>
          </div>

          {/* Features Preview */}
          <div className="grid grid-cols-3 gap-4 py-4">
            <div className="flex flex-col items-center space-y-2">
              <div className="w-12 h-12 rounded-full bg-accent-100/20 flex items-center justify-center">
                <Shield className="h-6 w-6 text-accent-200" />
              </div>
              <span className="text-xs text-muted-foreground">Threat Detection</span>
            </div>
            <div className="flex flex-col items-center space-y-2">
              <div className="w-12 h-12 rounded-full bg-accent-100/20 flex items-center justify-center">
                <Eye className="h-6 w-6 text-accent-200" />
              </div>
              <span className="text-xs text-muted-foreground">Email Monitoring</span>
            </div>
            <div className="flex flex-col items-center space-y-2">
              <div className="w-12 h-12 rounded-full bg-accent-100/20 flex items-center justify-center">
                <Chrome className="h-6 w-6 text-accent-200" />
              </div>
              <span className="text-xs text-muted-foreground">AI Analysis</span>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-6 pb-8">
          {/* Connect Button */}
          <Button
            onClick={handleGmailConnect}
            className="w-full h-12 text-base font-medium bg-gradient-accent hover:shadow-glow transition-all duration-300"
            size="lg"
          >
            <Chrome className="h-5 w-5 mr-3" />
            Connect with Gmail
          </Button>

          {/* Security Notice */}
          <div className="text-center">
            <p className="text-xs text-muted-foreground leading-relaxed">
              By connecting, you authorize SentinelAI to monitor your emails for security threats. 
              Your privacy and data security are our top priority.
            </p>
          </div>

          {/* Divider */}
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t border-border" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-card px-2 text-muted-foreground">Secure Authentication</span>
            </div>
          </div>

          {/* Trust Indicators */}
          <div className="flex justify-center space-x-6 text-xs text-muted-foreground">
            <div className="flex items-center space-x-1">
              <Shield className="h-3 w-3" />
              <span>256-bit SSL</span>
            </div>
            <div className="flex items-center space-x-1">
              <Eye className="h-3 w-3" />
              <span>OAuth 2.0</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}