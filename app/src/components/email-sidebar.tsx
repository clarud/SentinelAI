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
      
      // Set up interval to fetch emails every minute
      interval = setInterval(fetchEmails, 60000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isListening]);

  const fetchEmails = async () => {
    try {
      setIsLoading(true);
      const emailList = await apiClient.getEmailList();
      setEmails(emailList);
    } catch (error) {
      console.error('Failed to fetch emails:', error);
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
    <Card className="h-full p-4 border-r border-border">
      <div className="space-y-4">
        {/* Toggle Switch */}
        <div className="pb-4 border-b border-border animate-fade-in">
          <div className="transition-transform hover:scale-105">
            <ToggleSwitch
              label="Toggle email listen"
              checked={isListening}
              onCheckedChange={handleToggleListening}
            />
          </div>
          {isListening && (
            <p className={cn(
              "text-xs mt-2 flex items-center gap-1 transition-all duration-300 animate-pulse-soft",
              "text-accent-200"
            )}>
              <Clock className="h-3 w-3" />
              Checking every minute
            </p>
          )}
        </div>

        {/* Email List */}
        <div className="space-y-2">
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
                "w-full justify-start text-left h-auto p-3 transition-all duration-200 animate-fade-in hover:scale-[1.02] hover:shadow-md",
                selectedEmailId === emailId && "bg-accent-100 hover:bg-accent-100 shadow-md scale-[1.02]"
              )}
              style={{ animationDelay: `${index * 0.05}s` }}
              onClick={() => onEmailSelect(emailId)}
            >
              <Mail className="h-4 w-4 mr-2 flex-shrink-0 transition-transform hover:scale-110" />
              <span className="truncate">{emailId}</span>
            </Button>
          ))}
        </div>
      </div>
    </Card>
  );
}