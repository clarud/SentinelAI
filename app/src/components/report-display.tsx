import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { FileUpload } from '@/components/ui/file-upload';
import { Shield, AlertTriangle, CheckCircle, Info, Calendar, User, Mail, Download } from 'lucide-react';
import { ScamReport, apiClient } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';

interface ReportDisplayProps {
  selectedEmailId?: string;
  onReportChange: (report: ScamReport | null) => void;
}

export function ReportDisplay({ selectedEmailId, onReportChange }: ReportDisplayProps) {
  const [activeTab, setActiveTab] = useState('live');
  const [report, setReport] = useState<ScamReport | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [isDownloading, setIsDownloading] = useState(false);
  const { toast } = useToast();

  const handleFileUpload = async (file: File) => {
    setUploadedFile(file);
    setIsLoading(true);
    
    try {
      const result = await apiClient.uploadFile(file);
      setReport(result);
      onReportChange(result);
      toast({
        title: "File processed successfully",
        description: `${file.name} has been analyzed for threats.`,
      });
    } catch (error) {
      console.error('File upload failed:', error);
      toast({
        title: "Upload failed",
        description: "Failed to process the file. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const fetchEmailReport = async (emailId: string) => {
    setIsLoading(true);
    try {
      const result = await apiClient.getEmailReport(emailId);
      setReport(result);
      onReportChange(result);
    } catch (error) {
      console.error('Failed to fetch email report:', error);
      toast({
        title: "Failed to load email",
        description: "Unable to fetch the email report.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownload = async () => {
    if (!selectedEmailId) return;
    
    setIsDownloading(true);
    try {
      const driveLink = await apiClient.downloadReport(selectedEmailId);
      window.open(driveLink, '_blank');
      toast({
        title: "Download started",
        description: "Report is being downloaded from Google Drive.",
      });
    } catch (error) {
      console.error('Download failed:', error);
      toast({
        title: "Download failed",
        description: "Failed to download the report. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsDownloading(false);
    }
  };

  const fetchEmailDetails = async (emailId: string) => {
    setIsLoading(true);
    try {
      const userEmail = sessionStorage.getItem("user_email");
      if (!userEmail) return;

      const response = await fetch(`https://sentinelai-services.onrender.com/api/firestore/emails/${userEmail}/${emailId}`);
      if (!response.ok) {
        throw new Error("Failed to fetch email details");
      }
      const data = await response.json();
      setReport(data);
      onReportChange(data);
    } catch (error) {
      console.error("Failed to fetch email details:", error);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle email selection in live mode
  React.useEffect(() => {
    if (activeTab === 'live' && selectedEmailId) {
      fetchEmailDetails(selectedEmailId);
    }
  }, [selectedEmailId, activeTab]);



  const getScamIcon = (scamType: string) => {
    switch (scamType.toLowerCase()) {
      case 'scam':
        return <AlertTriangle className="h-5 w-5 text-destructive" />;
      case 'not_scam':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'suspicious':
        return <Shield className="h-5 w-5 text-yellow-600" />;
      default:
        return <Info className="h-5 w-5 text-muted-foreground" />;
    }
  };

  const getScamBadgeVariant = (scamType: string) => {
    switch (scamType.toLowerCase()) {
      case 'scam':
        return 'destructive';
      case 'not_scam':
        return 'default';
      case 'suspicious':
        return 'secondary';
      default:
        return 'outline';
    }
  };

  return (
    <Card className="h-full animate-fade-in">
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 animate-slide-in-right">
            <Shield className="h-5 w-5 text-accent-200" />
            Analysis Report
          </CardTitle>
          {activeTab === 'live' && report && selectedEmailId && (
            <Button
              onClick={handleDownload}
              disabled={isDownloading}
              variant="outline"
              size="sm"
              className="transition-all duration-200 hover:scale-105 hover:shadow-md"
            >
              <Download className="h-4 w-4 mr-2" />
              {isDownloading ? 'Downloading...' : 'Download'}
            </Button>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-2 transition-all duration-200">
            <TabsTrigger 
              value="live" 
              className="transition-all duration-200 hover:scale-105"
            >
              Live
            </TabsTrigger>
            <TabsTrigger 
              value="upload"
              className="transition-all duration-200 hover:scale-105"
            >
              Upload
            </TabsTrigger>
          </TabsList>

          <TabsContent value="upload" className="space-y-4 animate-fade-in-up">
            <h3 className="font-medium text-foreground">Upload File for Analysis</h3>
            <div className="transition-all duration-300 hover:scale-[1.01]">
              <FileUpload onFileSelect={handleFileUpload} />
            </div>
            {uploadedFile && (
              <p className="text-sm text-muted-foreground animate-fade-in">
                Selected: {uploadedFile.name}
              </p>
            )}
          </TabsContent>

          <TabsContent value="live" className="animate-fade-in-up">
            {/* Live mode content will be shown below */}
          </TabsContent>
        </Tabs>

        {/* Loading State */}
        {isLoading && (
          <div className="flex items-center justify-center py-12 animate-fade-in">
            <div className="text-center">
              <LoadingSpinner size="lg" />
              <p className="mt-4 text-muted-foreground animate-pulse-soft">Analyzing content...</p>
            </div>
          </div>
        )}

        {/* Report Content */}
        {!isLoading && report && (
          <div className="space-y-6 animate-fade-in-up">
            {/* Email Information */}
            {report.email && (
              <div className="space-y-4 animate-scale-in">
                <h3 className="font-semibold text-foreground flex items-center gap-2 transition-colors hover:text-accent-200">
                  <Mail className="h-4 w-4 transition-transform hover:scale-110" />
                  Email Details
                </h3>
                <div className="grid gap-3 p-4 bg-muted/30 rounded-lg transition-all duration-300 hover:bg-muted/40 hover:shadow-md">
                  <div className="flex items-center gap-2 transition-all hover:translate-x-1">
                    <User className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm font-medium">From:</span>
                    <span className="text-sm">{report.email.sender}</span>
                  </div>
                  <div className="flex items-center gap-2 transition-all hover:translate-x-1">
                    <Mail className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm font-medium">To:</span>
                    <span className="text-sm">{report.email.to}</span>
                  </div>
                  <div className="flex items-center gap-2 transition-all hover:translate-x-1">
                    <Calendar className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm font-medium">Date:</span>
                    <span className="text-sm">{report.email.date}</span>
                  </div>
                  <div className="transition-all hover:translate-x-1">
                    <span className="text-sm font-medium">Subject:</span>
                    <p className="text-sm mt-1">{report.email.subject}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Scam Analysis */}
            <div className="space-y-4 animate-scale-in" style={{ animationDelay: '0.1s' }}>
              <h3 className="font-semibold text-foreground flex items-center gap-2 transition-colors hover:text-accent-200">
                <Shield className="h-4 w-4 transition-transform hover:scale-110" />
                Security Analysis
              </h3>
              <div className="grid gap-4 p-4 bg-muted/30 rounded-lg transition-all duration-300 hover:bg-muted/40 hover:shadow-md">
                <div className="flex items-center justify-between transition-all hover:scale-[1.02]">
                  <span className="text-sm font-medium">Threat Classification:</span>
                  <Badge 
                    variant={getScamBadgeVariant(report.is_scam)}
                    className="flex items-center gap-1 transition-all duration-200 hover:scale-105"
                  >
                    {getScamIcon(report.is_scam)}
                    {report.is_scam.replace('_', ' ').toUpperCase()}
                  </Badge>
                </div>
                
                <div className="flex items-center justify-between transition-all hover:scale-[1.02]">
                  <span className="text-sm font-medium">Confidence Level:</span>
                  <div className="flex items-center gap-2">
                    <div className="w-24 h-2 bg-muted rounded-full overflow-hidden">
                      <div 
                        className={cn(
                          "h-full transition-all duration-500 animate-slide-in-right",
                          report.confidence_level >= 0.8 ? "bg-green-500" :
                          report.confidence_level >= 0.6 ? "bg-yellow-500" : "bg-red-500"
                        )}
                        style={{ width: `${report.confidence_level * 100}%` }}
                      />
                    </div>
                    <span className="text-sm font-mono">
                      {(report.confidence_level * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>
                
                <div className="flex items-center justify-between transition-all hover:scale-[1.02]">
                  <span className="text-sm font-medium">Threat Probability:</span>
                  <span className="text-sm font-mono">
                    {report.scam_probability.toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>

            {/* Explanation */}
            <div className="space-y-2 animate-scale-in" style={{ animationDelay: '0.2s' }}>
              <h3 className="font-semibold text-foreground transition-colors hover:text-accent-200">Analysis Explanation</h3>
              <p className="text-sm text-muted-foreground leading-relaxed p-4 bg-muted/30 rounded-lg transition-all duration-300 hover:bg-muted/40 hover:shadow-md">
                {report.explanation}
              </p>
            </div>
          </div>
        )}

        {/* Empty States */}
        {!isLoading && !report && activeTab === 'live' && (
          <div className="text-center py-12 text-muted-foreground animate-fade-in">
            <Shield className="h-12 w-12 mx-auto mb-4 opacity-50 animate-bounce-soft" />
            <p>Select an email from the sidebar to view its analysis</p>
          </div>
        )}

        {!isLoading && !report && activeTab === 'upload' && (
          <div className="text-center py-12 text-muted-foreground animate-fade-in">
            <Shield className="h-12 w-12 mx-auto mb-4 opacity-50 animate-bounce-soft" />
            <p>Upload a file to begin security analysis</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default ReportDisplay;