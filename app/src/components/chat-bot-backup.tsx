import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { MessageCircle, Send, Bot, User } from 'lucide-react';
import { ChatMessage, ScamReport, apiClient } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';
import { cn } from '@/lib/utils';

interface ChatBotProps {
  currentReport?: ScamReport | null;
}

export function ChatBot({ currentReport }: ChatBotProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content: "Hello! I'm here to help you with fraud detection and cybersecurity questions. How can I assist you today?"
    }
  ]);
  const [currentInput, setCurrentInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();

  // Scroll to bottom whenever messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Scroll to bottom when loading state changes (for the "Thinking..." message)
  useEffect(() => {
    if (isLoading) {
      scrollToBottom();
    }
  }, [isLoading]);

  const scrollToBottom = () => {
    // Use requestAnimationFrame to ensure the scroll happens after DOM updates
    requestAnimationFrame(() => {
      if (messagesEndRef.current) {
        messagesEndRef.current.scrollIntoView({ 
          behavior: 'smooth',
          block: 'nearest'
        });
      } else if (scrollAreaRef.current) {
        // Fallback to scrollArea if messagesEndRef isn't available
        scrollAreaRef.current.scrollTo({ 
          top: scrollAreaRef.current.scrollHeight, 
          behavior: 'smooth' 
        });
      }
    });
  };

  const handleSendMessage = async () => {
    if (!currentInput.trim()) return;

    const userMessage: ChatMessage = {
      role: "user",
      content: currentInput
    };

    setMessages((prevMessages) => [...prevMessages, userMessage]);
    setCurrentInput('');
    setIsLoading(true);

    try {
      const context = currentReport ? JSON.stringify(currentReport) : '';
      const response = await apiClient.chat({
        context,
        current_input: currentInput,
        history: messages // Pass the history without appending the user message again
      });

      // Append only the latest assistant response to the chat
      const latestResponse = response.history[response.history.length - 1];
      setMessages((prevMessages) => [...prevMessages, latestResponse]);
    } catch (error) {
      console.error('Chat request failed:', error);
      toast({
        title: "Chat Error",
        description: "Failed to send message. Please try again.",
        variant: "destructive",
      });

      const errorMessage: ChatMessage = {
        role: "assistant",
        content: "I'm sorry, I'm having trouble responding right now. Please try again in a moment."
      };
      setMessages((prevMessages) => [...prevMessages, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="h-full flex flex-col animate-fade-in bg-gradient-card/80 backdrop-blur-sm">
      <div className="pb-4 px-4 pt-4 border-b border-border/30">
        <div className="flex items-center gap-3 animate-slide-in-right p-3 rounded-xl bg-surface-100/50 border border-border/20 shadow-subtle">
          <div className="p-2 rounded-lg bg-gradient-primary/30">
            <MessageCircle className="h-5 w-5 text-cyber-blue transition-transform hover:scale-110" />
          </div>
          <h3 className="font-semibold text-foreground">Security Assistant</h3>
        </div>
      </div>

      <div className="flex-1 flex flex-col p-4 space-y-4 overflow-hidden">
        {/* Messages Area */}
        <ScrollArea className="flex-1 pr-4 overflow-y-auto" ref={scrollAreaRef}>
          <div className="space-y-4">
            {messages.map((message, index) => (
              <div
                key={index}
                className={cn(
                  "flex gap-3 animate-fade-in-up",
                  message.role === "user" ? "justify-end" : "justify-start"
                )}
                style={{ animationDelay: `${index * 0.1}s` }}
              >
                <div
                  className={cn(
                    "flex gap-3 max-w-[80%]",
                    message.role === "user" ? "flex-row-reverse" : "flex-row"
                  )}
                >
                  <div className={cn(
                    "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center transition-transform hover:scale-110 shadow-medium border",
                    message.role === "user" 
                      ? "bg-gradient-accent text-white border-cyber-blue/30" 
                      : "bg-gradient-card/80 text-muted-foreground border-border/20 backdrop-blur-sm"
                  )}>
                    {message.role === "user" ? (
                      <User className="h-4 w-4" />
                    ) : (
                      <Bot className="h-4 w-4 text-cyber-blue" />
                    )}
                  </div>
                  
                  <div
                    className={cn(
                      "rounded-xl px-4 py-3 text-sm transition-all duration-200 hover:scale-[1.02] hover:shadow-medium border backdrop-blur-sm",
                      message.role === "user"
                        ? "bg-gradient-accent text-white border-cyber-blue/30 shadow-cyber"
                        : "bg-surface-100/80 text-foreground border-border/20"
                    )}
                  >
                    <p className="whitespace-pre-wrap">{message.content}</p>
                  </div>
                </div>
              </div>
            ))}
            
            {isLoading && (
              <div className="flex gap-3 justify-start animate-fade-in">
                <div className="flex gap-3 max-w-[80%]">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-card/80 text-muted-foreground flex items-center justify-center border border-border/20 backdrop-blur-sm">
                    <Bot className="h-4 w-4 text-cyber-blue" />
                  </div>
                  <div className="bg-surface-100/80 text-foreground rounded-xl px-4 py-3 text-sm flex items-center gap-2 border border-border/20 backdrop-blur-sm">
                    <LoadingSpinner size="sm" />
                    <span className="animate-pulse-soft">Thinking...</span>
                  </div>
                </div>
              </div>
            )}
            
            {/* Invisible element at the bottom to scroll to */}
            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>

        {/* Input Area */}
        <div className="flex gap-3 animate-fade-in-up p-3 rounded-xl bg-surface-100/50 border border-border/20 shadow-subtle">
          <Input
            placeholder="Ask about security threats, email analysis, or cybersecurity..."
            value={currentInput}
            onChange={(e) => setCurrentInput(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={isLoading}
            className="flex-1 transition-all duration-200 focus:scale-[1.01] border-cyber-blue/20 focus:border-cyber-blue/40 bg-surface-100/80 backdrop-blur-sm"
          />
          <Button
            onClick={handleSendMessage}
            disabled={isLoading || !currentInput.trim()}
            size="icon"
            className="flex-shrink-0 transition-all duration-200 hover:scale-110 hover:shadow-cyber bg-gradient-accent border-0"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>

        {/* Context Indicator */}
        {currentReport && (
          <div className="text-xs text-muted-foreground border-t border-border/30 pt-3 animate-fade-in transition-colors hover:text-cyber-blue px-3 py-2 rounded-lg bg-cyber-blue/5">
            💡 Chat context includes the current analysis report
          </div>
        )}
      </div>
    </div>
  );
}