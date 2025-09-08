import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { EmailSidebar } from '@/components/email-sidebar';
import { ReportDisplay } from '@/components/report-display';
import { ChatBot } from '@/components/chat-bot';
import { Button } from '@/components/ui/button';
import { ScamReport } from '@/lib/api';
import { Shield, LogOut } from 'lucide-react';
import sentinelLogo from '@/assets/SentinelAILogo.png';

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
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-10 animate-fade-in">
        <div className="flex items-center justify-between p-4">
          <div className="flex items-center gap-3">
            <img 
              src={sentinelLogo} 
              alt="SentinelAI" 
              className="w-8 h-8 transition-transform hover:scale-110"
            />
            <h1 className="text-xl font-bold bg-gradient-accent bg-clip-text text-transparent animate-slide-in-right">
              SentinelAI
            </h1>
            <Shield className="h-5 w-5 text-accent-200 ml-1 animate-glow" />
          </div>
          
          <div className="flex items-center gap-4">
            {user_email && (
              <span className="text-sm text-muted-foreground">
                {user_email}
              </span>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={handleLogout}
              className="transition-all duration-200 hover:scale-105 hover:bg-destructive hover:text-destructive-foreground"
            >
              <LogOut className="h-4 w-4 mr-2" />
              Log out
            </Button>
          </div>
        </div>
      </header>

      {/* Main Layout */}
      <div className="flex h-[calc(100vh-73px)]">
        {/* Left Sidebar - Email List */}
        <div className="w-80 border-r border-border animate-slide-in">
          <EmailSidebar
            onEmailSelect={setSelectedEmailId}
            selectedEmailId={selectedEmailId}
          />
        </div>

        {/* Middle Section - Report Display */}
        <div className="flex-1 border-r border-border animate-fade-in" style={{ animationDelay: '0.1s' }}>
          <ReportDisplay
            selectedEmailId={selectedEmailId}
            onReportChange={setCurrentReport}
          />
        </div>

        {/* Right Section - Chat Bot */}
        <div className="w-96 animate-slide-in-right" style={{ animationDelay: '0.2s' }}>
          <ChatBot report={currentReport} />
        </div>
      </div>
    </div>
  );
}