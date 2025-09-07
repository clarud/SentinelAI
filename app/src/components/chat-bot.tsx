import { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { MessageCircle, Send, Bot, User } from 'lucide-react';
import { ChatMessage, ScamReport, apiClient } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';
import { cn } from '@/lib/utils';

interface ChatBotProps {
  report: ScamReport | null;
}

export function ChatBot({ report }: ChatBotProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content: "Hello! I'm here to help you with fraud detection and cybersecurity questions. How can I assist you today?"
    }
  ]);
  const [currentInput, setCurrentInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();

  useEffect(() => {
    // Scroll to bottom when new messages are added
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSendMessage = async () => {
    if (!currentInput.trim()) return;

    const userMessage: ChatMessage = {
      role: "user",
      content: currentInput
    };

    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setCurrentInput('');
    setIsLoading(true);

    try {
      const context = report ? JSON.stringify(report) : '';
      const response = await apiClient.chat({
        context,
        current_input: currentInput,
        history: newMessages
      });

      setMessages(response.history);
    } catch (error) {
      console.error('Chat request failed:', error);
      toast({
        title: "Chat Error",
        description: "Failed to send message. Please try again.",
        variant: "destructive",
      });
      
      // Add error message to chat
      const errorMessage: ChatMessage = {
        role: "assistant",
        content: "I'm sorry, I'm having trouble responding right now. Please try again in a moment."
      };
      setMessages([...newMessages, errorMessage]);
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
    <Card className="h-full flex flex-col animate-fade-in">
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center gap-2 animate-slide-in-right">
          <MessageCircle className="h-5 w-5 text-accent-200 transition-transform hover:scale-110" />
          Security Assistant
        </CardTitle>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col p-4 space-y-4">
        {/* Messages Area */}
        <ScrollArea className="flex-1 pr-4" ref={scrollAreaRef}>
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
                    "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center transition-transform hover:scale-110",
                    message.role === "user" 
                      ? "bg-accent-200 text-white" 
                      : "bg-muted text-muted-foreground"
                  )}>
                    {message.role === "user" ? (
                      <User className="h-4 w-4" />
                    ) : (
                      <Bot className="h-4 w-4" />
                    )}
                  </div>
                  
                  <div
                    className={cn(
                      "rounded-lg px-4 py-2 text-sm transition-all duration-200 hover:scale-[1.02] hover:shadow-md",
                      message.role === "user"
                        ? "bg-accent-200 text-white"
                        : "bg-muted text-foreground"
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
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-muted text-muted-foreground flex items-center justify-center">
                    <Bot className="h-4 w-4" />
                  </div>
                  <div className="bg-muted text-foreground rounded-lg px-4 py-2 text-sm flex items-center gap-2">
                    <LoadingSpinner size="sm" />
                    <span className="animate-pulse-soft">Thinking...</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </ScrollArea>

        {/* Input Area */}
        <div className="flex gap-2 animate-fade-in-up">
          <Input
            placeholder="Ask about security threats, email analysis, or cybersecurity..."
            value={currentInput}
            onChange={(e) => setCurrentInput(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={isLoading}
            className="flex-1 transition-all duration-200 focus:scale-[1.01]"
          />
          <Button
            onClick={handleSendMessage}
            disabled={isLoading || !currentInput.trim()}
            size="icon"
            className="flex-shrink-0 transition-all duration-200 hover:scale-110 hover:shadow-md"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>

        {/* Context Indicator */}
        {report && (
          <div className="text-xs text-muted-foreground border-t pt-2 animate-fade-in transition-colors hover:text-accent-200">
            💡 Chat context includes the current analysis report
          </div>
        )}
      </CardContent>
    </Card>
  );
}