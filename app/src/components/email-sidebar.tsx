import { useState, useEffect } from 'react';
import { ToggleSwitch } from '@/components/ui/toggle-switch';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { Mail, Clock } from 'lucide-react';
import { apiClient } from '@/lib/api';
import { cn } from '@/lib/utils';

interface EmailSidebarProps {
  onEmailSelect: (emailId: string) => void;
  selectedEmailId?: string;
}

export function EmailSidebar({ onEmailSelect, selectedEmailId }: EmailSidebarProps) {
  const [isListening, setIsListening] = useState(false);
  const [emails, setEmails] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    
    if (isListening) {
      // Fetch emails immediately when listening starts
      fetchEmails();
      
      // Set up interval to fetch emails every 10 seconds
      interval = setInterval(fetchEmails, 30000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isListening]);

  const fetchEmails = async () => {
    try {
      setIsLoading(true);
      const userEmail = sessionStorage.getItem("user_email");
      if (!userEmail) return;

      const response = await fetch(`https://sentinelai-services.onrender.com/api/firestore/emails/${userEmail}`);
      if (!response.ok) {
        throw new Error("Failed to fetch email IDs");
      }
      const emailList = await response.json();
      console.log("Fetched emails:", emailList);
      // Reverse the order to show newest first
      setEmails(emailList.reverse());
    } catch (error) {
      console.error("Failed to fetch emails:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggleListening = (checked: boolean) => {
    setIsListening(checked);
    if (!checked) {
      setEmails([]);
    }
  };

  return (
    <div className="h-full p-4 flex flex-col bg-gradient-card/80 backdrop-blur-sm">
      <div className="flex flex-col h-full space-y-4">
        {/* Toggle Switch */}
        <div className="pb-4 border-b border-white/30 animate-fade-in flex-shrink-0">
          <div className="transition-transform hover:scale-105 p-3 rounded-xl bg-surface-100/50 border border-white/20 shadow-subtle">
            <ToggleSwitch
              label="Toggle email listen"
              checked={isListening}
              onCheckedChange={handleToggleListening}
            />
          </div>
          {isListening && (
            <p className={cn(
              "text-xs mt-3 flex items-center gap-1 transition-all duration-300 animate-pulse-soft px-3 py-2 rounded-lg bg-cyber-blue/10 border border-cyber-blue/20",
              "text-cyber-blue font-medium"
            )}>
              <Clock className="h-3 w-3" />
              Checking every minute
            </p>
          )}
        </div>

        {/* Email List - Scrollable */}
        <div className="flex-1 overflow-y-auto space-y-2 min-h-0">
          {isLoading && (
            <div className="flex items-center justify-center py-8 animate-fade-in">
              <LoadingSpinner />
            </div>
          )}
          
          {!isLoading && emails.length === 0 && isListening && (
            <div className="text-center py-8 text-muted-foreground animate-fade-in">
              <Mail className="h-8 w-8 mx-auto mb-2 animate-bounce-soft" />
              <p className="text-sm">No emails found</p>
            </div>
          )}
          
          {!isLoading && emails.length === 0 && !isListening && (
            <div className="text-center py-8 text-muted-foreground animate-fade-in">
              <Mail className="h-8 w-8 mx-auto mb-2 animate-bounce-soft" />
              <p className="text-sm">Enable email listening to start</p>
            </div>
          )}

          {emails.map((emailId, index) => (
            <Button
              key={emailId}
              variant={selectedEmailId === emailId ? "default" : "ghost"}
              className={cn(
                "w-full justify-start text-left h-auto p-4 transition-all duration-200 animate-fade-in hover:scale-[1.02] hover:shadow-medium rounded-xl border",
                selectedEmailId === emailId 
                  ? "bg-gradient-primary/80 hover:bg-gradient-primary border-cyber-blue/30 shadow-cyber text-primary-300" 
                  : "bg-surface-100/50 hover:bg-surface-100/80 border-white/20 hover:border-cyber-blue/20 backdrop-blur-sm"
              )}
              style={{ animationDelay: `${index * 0.05}s` }}
              onClick={async () => {
                onEmailSelect(emailId);
                const userEmail = sessionStorage.getItem("user_email");
                if (!userEmail) return;

                try {
                  const response = await fetch(`https://sentinelai-services.onrender.com/api/firestore/emails/${userEmail}/${emailId}`);
                  if (!response.ok) {
                    throw new Error("Failed to fetch email details");
                  }
                  const emailDetails = await response.json();
                  console.log("Email details:", emailDetails);
                  // Pass the email details to the report-display component
                  // This assumes a shared state or context is used to pass data
                } catch (error) {
                  console.error("Failed to fetch email details:", error);
                }
              }}
            >
              <Mail className={cn(
                "h-4 w-4 mr-3 flex-shrink-0 transition-all duration-200",
                selectedEmailId === emailId ? "text-cyber-blue scale-110" : "text-muted-foreground group-hover:text-cyber-blue"
              )} />
              <span className="truncate font-medium">{emailId}</span>
            </Button>
          ))}
        </div>
      </div>
    </div>
  );
}