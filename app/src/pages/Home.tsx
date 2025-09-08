import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { EmailSidebar } from '@/components/email-sidebar';
import { ReportDisplay } from '@/components/report-display';
import { ChatBot } from '@/components/chat-bot';
import { ThemeToggle } from '@/components/theme-toggle';
import { Button } from '@/components/ui/button';
import { ScamReport } from '@/lib/api';
import { Shield, LogOut } from 'lucide-react';
import sentinelLogo from '@/assets/SentinelAI_Logo.png';

export default function Home() {
  const { user_email } = useParams();
  const navigate = useNavigate();
  const [selectedEmailId, setSelectedEmailId] = useState<string>();
  const [currentReport, setCurrentReport] = useState<ScamReport | null>(null);

  useEffect(() => {
    if (user_email) {
      // Store the user email in session storage
      sessionStorage.setItem('user_email', user_email);
    }
  }, [user_email]);

  const handleLogout = async () => {
    const userEmail = sessionStorage.getItem('user_email') || user_email;
    
    // Stop email watching if user email is available
    if (userEmail) {
      try {
        const response = await fetch(`https://sentinelai-services.onrender.com/api/stop-watch/${userEmail}`, {
          method: 'POST',
        });
        if (!response.ok) {
          console.warn('Failed to stop email watching:', response.statusText);
        }
      } catch (error) {
        console.error('Error stopping email watch:', error);
      }
    }
    
    // Clear session storage
    sessionStorage.removeItem('user_email');
    // Redirect to login page (assuming root path is login)
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-gradient-hero relative overflow-hidden">
      {/* Background Pattern */}
      <div className="absolute inset-0">
        <div className="absolute top-0 left-0 w-full h-full bg-gradient-cyber opacity-30"></div>
        <div className="absolute top-1/3 right-1/4 w-64 h-64 bg-cyber-blue/5 rounded-full blur-3xl"></div>
        <div className="absolute bottom-1/3 left-1/4 w-96 h-96 bg-cyber-teal/3 rounded-full blur-3xl"></div>
      </div>

      {/* Header */}
      <header className="border-b border-white/30 bg-gradient-card/80 backdrop-blur-md sticky top-0 z-10 animate-fade-in shadow-medium">
        <div className="flex items-center justify-between p-4">
          <div className="flex items-center gap-3">
            <div className="p-1 rounded-xl bg-gradient-primary/20 shadow-subtle">
              <img 
                src={sentinelLogo} 
                alt="SentinelAI" 
                className="w-8 h-8 transition-transform hover:scale-110"
              />
            </div>
            <h1 className="text-xl font-bold bg-gradient-accent bg-clip-text text-transparent animate-slide-in-right">
              SentinelAI
            </h1>
            <Shield className="h-5 w-5 text-cyber-blue ml-1 animate-glow" />
          </div>
          
          <div className="flex items-center gap-4">
            <ThemeToggle />
            {user_email && (
              <span className="text-sm text-muted-foreground px-3 py-1 rounded-full bg-surface-200/50 backdrop-blur-sm border border-white/20">
                {user_email}
              </span>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={handleLogout}
              className="transition-all duration-200 hover:scale-105 hover:bg-destructive/10 hover:text-destructive border border-white/20 hover:border-destructive/20 hover:shadow-medium"
            >
              <LogOut className="h-4 w-4 mr-2" />
              Log out
            </Button>
          </div>
        </div>
      </header>

            {/* Main Layout */}
      <div className="flex h-[calc(100vh-73px)] relative z-10">
        {/* Left Sidebar - Email List */}
        <div className="w-80 border-r border-white/30 bg-gradient-card/60 backdrop-blur-sm animate-slide-in shadow-medium">
          <EmailSidebar
            onEmailSelect={setSelectedEmailId}
            selectedEmailId={selectedEmailId}
          />
        </div>

        {/* Middle Section - Report Display */}
        <div className="flex-1 border-r border-white/30 bg-gradient-card/40 backdrop-blur-sm animate-fade-in shadow-medium" style={{ animationDelay: '0.1s' }}>
          <ReportDisplay
            selectedEmailId={selectedEmailId}
            onReportChange={setCurrentReport}
          />
        </div>

        {/* Right Sidebar - ChatBot */}
        <div className="w-80 bg-gradient-card/60 backdrop-blur-sm animate-slide-in-right shadow-medium" style={{ animationDelay: '0.2s' }}>
          <ChatBot currentReport={currentReport} />
        </div>
      </div>
    </div>
  );
}