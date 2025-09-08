const API_BASE_URL = "https://sentinelai-services.onrender.com";

export interface EmailData {
  id: string;
  sender: string;
  subject: string;
  date: string;
  to: string;
  snippet: string;
  threadId: string;
  body: string;
  body_preview: string;
  email_address: string;
}

export interface ScamReport {
  is_scam: string;
  confidence_level: number;
  scam_probability: number;
  explanation: string;
  text: string;
  email: EmailData;
  tool_evidence?: Array<Record<string, any>>;
  tool_errors?: Array<Record<string, any>>;
  processing_metadata: Record<string, any>;
  drive_analysis_link?: string; // Added field for Google Drive link of analysis report
}

export interface UploadResponse {
  task_id: string;
}

export interface TaskResult {
  state: "PENDING" | "SUCCESS" | "FAILURE";
  result?: {
    text?: string;
    assessment?: ScamReport;
  };
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatRequest {
  context: string;
  current_input: string;
  history: ChatMessage[];
}

export interface ChatResponse {
  response: string;
  history: ChatMessage[];
  intent: string;
}

export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  async connectGmail(): Promise<void> {
    window.location.href = `${this.baseUrl}/api/connect-gmail`;
  }

  async uploadFile(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/api/jobs/file`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Failed to upload file: ${response.statusText}`);
    }

    return response.json();
  }

  async chat(request: ChatRequest): Promise<ChatResponse> {
    const response = await fetch(`${this.baseUrl}/api/jobs/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Chat request failed: ${response.statusText}`);
    }

    return response.json();
  }

  async sendChatMessage(message: string, context: string = '', history: ChatMessage[] = []): Promise<ChatResponse> {
    const request: ChatRequest = {
      current_input: message,
      context: context,
      history: history
    };

    return this.chat(request);
  }

  async getTaskStatus(taskId: string): Promise<any> {
    const response = await fetch(`${this.baseUrl}/api/jobs/tasks/${taskId}`, {
      method: 'GET',
    });

    if (!response.ok) {
      throw new Error(`Failed to get task status: ${response.statusText}`);
    }

    return response.json();
  }

  // Mock function for getting email list - replace with actual API call
  async getEmailList(): Promise<string[]> {
    // This would be replaced with actual API call once endpoint is available
    return Promise.resolve([]);
  }

  // Mock function for getting email report - replace with actual API call
  async getEmailReport(emailId: string): Promise<ScamReport> {
    // This would be replaced with actual API call once endpoint is available
    throw new Error("Email report endpoint not yet implemented");
  }

  async downloadReport(emailId: string): Promise<string> {
    const response = await fetch(`${this.baseUrl}/api/jobs/download/${emailId}`);
    if (!response.ok) {
      throw new Error('Failed to download report');
    }
    const data = await response.json();
    return data.google_drive_link;
  }
}

export const apiClient = new ApiClient();