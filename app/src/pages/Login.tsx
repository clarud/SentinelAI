import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { ThemeToggle } from '@/components/theme-toggle';
import { Shield, Eye, Chrome } from 'lucide-react';
import { apiClient } from '@/lib/api';
import sentinelLogo from '@/assets/SentinelAI_Logo.png';

export default function Login() {
  const handleGmailConnect = () => {
    apiClient.connectGmail();
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-hero p-4 relative overflow-hidden">
      {/* Theme Toggle */}
      <div className="absolute top-6 right-6 z-20">
        <ThemeToggle />
      </div>
      
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-cyber-blue/10 rounded-full blur-3xl animate-pulse-soft"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-cyber-teal/8 rounded-full blur-3xl animate-bounce-soft"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-128 h-128 bg-gradient-cyber rounded-full blur-3xl opacity-30"></div>
      </div>
      
      <Card className="w-full max-w-md shadow-cyber bg-gradient-card backdrop-blur-sm border border-white/20 relative z-10">
        <CardHeader className="text-center space-y-6 pt-8">
          {/* Logo and Branding */}
          <div className="flex flex-col items-center space-y-4">
            <div className="relative bg-transparent p-2 rounded-2xl bg-gradient-primary/20">
              <img 
                src={sentinelLogo} 
                alt="SentinelAI Logo" 
                className="w-20 h-20 bg-transparent animate-scale-in"
                style={{ 
                  backgroundColor: 'transparent !important',
                  background: 'none',
                  boxShadow: 'none'
                }}
              />
            </div>
            
            <div className="space-y-2">
              <h1 className="text-3xl font-bold bg-gradient-accent bg-clip-text text-transparent animate-fade-in">
                SentinelAI
              </h1>
              <p className="text-muted-foreground text-sm font-medium animate-fade-in-up">
                Always Watching, Always Protecting
              </p>
            </div>
          </div>

          {/* Features Preview */}
          <div className="grid grid-cols-3 gap-4 py-4">
            <div className="flex flex-col items-center space-y-2 animate-fade-in" style={{ animationDelay: '0.2s' }}>
              <div className="w-12 h-12 rounded-full bg-gradient-primary/30 backdrop-blur-sm flex items-center justify-center shadow-medium border border-cyber-blue/20 hover:shadow-glow transition-all duration-300">
                <Shield className="h-6 w-6 text-cyber-blue" />
              </div>
              <span className="text-xs text-muted-foreground font-medium">Threat Detection</span>
            </div>
            <div className="flex flex-col items-center space-y-2 animate-fade-in" style={{ animationDelay: '0.3s' }}>
              <div className="w-12 h-12 rounded-full bg-gradient-primary/30 backdrop-blur-sm flex items-center justify-center shadow-medium border border-cyber-teal/20 hover:shadow-glow transition-all duration-300">
                <Eye className="h-6 w-6 text-cyber-teal" />
              </div>
              <span className="text-xs text-muted-foreground font-medium">Email Monitoring</span>
            </div>
            <div className="flex flex-col items-center space-y-2 animate-fade-in" style={{ animationDelay: '0.4s' }}>
              <div className="w-12 h-12 rounded-full bg-gradient-primary/30 backdrop-blur-sm flex items-center justify-center shadow-medium border border-accent-200/20 hover:shadow-glow transition-all duration-300">
                <Chrome className="h-6 w-6 text-accent-200" />
              </div>
              <span className="text-xs text-muted-foreground font-medium">AI Analysis</span>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-6 pb-8">
          {/* Connect Button */}
          <Button
            onClick={handleGmailConnect}
            className="w-full h-12 text-base font-medium bg-gradient-accent hover:shadow-cyber transition-all duration-300 transform hover:scale-[1.02] hover:-translate-y-0.5 border-0 animate-fade-in-up"
            style={{ animationDelay: '0.5s' }}
            size="lg"
          >
            <Chrome className="h-5 w-5 mr-3" />
            Connect with Gmail
          </Button>

          {/* Security Notice */}
          <div className="text-center animate-fade-in-up" style={{ animationDelay: '0.6s' }}>
            <p className="text-xs text-muted-foreground leading-relaxed">
              By connecting, you authorize SentinelAI to monitor your emails for security threats. 
              Your privacy and data security are our top priority.
            </p>
          </div>

          {/* Divider */}
          <div className="relative animate-fade-in-up" style={{ animationDelay: '0.7s' }}>
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t border-border/50" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-card/80 backdrop-blur-sm px-3 py-1 text-muted-foreground rounded-full border border-border/30">Secure Authentication</span>
            </div>
          </div>

          {/* Trust Indicators */}
          <div className="flex justify-center space-x-6 text-xs text-muted-foreground animate-fade-in-up" style={{ animationDelay: '0.8s' }}>
            <div className="flex items-center space-x-1 px-2 py-1 rounded-full bg-surface-200/50 backdrop-blur-sm">
              <Shield className="h-3 w-3 text-cyber-blue" />
              <span>256-bit SSL</span>
            </div>
            <div className="flex items-center space-x-1 px-2 py-1 rounded-full bg-surface-200/50 backdrop-blur-sm">
              <Eye className="h-3 w-3 text-cyber-teal" />
              <span>OAuth 2.0</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}