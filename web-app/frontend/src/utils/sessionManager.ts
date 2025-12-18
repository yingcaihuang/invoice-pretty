// Session management utilities

export class SessionManager {
  private static readonly SESSION_KEY = 'web-invoice-processor-session';
  private static readonly TASKS_KEY = 'web-invoice-processor-tasks';
  private static readonly SESSION_CREATED_KEY = 'web-invoice-processor-session-created';

  static generateSessionId(): string {
    // Generate a cryptographically secure session ID
    const array = new Uint8Array(16);
    crypto.getRandomValues(array);
    const hex = Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
    return 'session_' + hex + '_' + Date.now();
  }

  static getSessionId(): string {
    let sessionId = localStorage.getItem(this.SESSION_KEY);
    if (!sessionId) {
      sessionId = this.generateSessionId();
      localStorage.setItem(this.SESSION_KEY, sessionId);
      localStorage.setItem(this.SESSION_CREATED_KEY, new Date().toISOString());
    }
    return sessionId;
  }

  static getSessionCreatedAt(): Date | null {
    const created = localStorage.getItem(this.SESSION_CREATED_KEY);
    return created ? new Date(created) : null;
  }

  static clearSession(): void {
    localStorage.removeItem(this.SESSION_KEY);
    localStorage.removeItem(this.TASKS_KEY);
    localStorage.removeItem(this.SESSION_CREATED_KEY);
  }

  static getStoredTasks(): string[] {
    const tasks = localStorage.getItem(this.TASKS_KEY);
    return tasks ? JSON.parse(tasks) : [];
  }

  static addTask(taskId: string): void {
    const tasks = this.getStoredTasks();
    if (!tasks.includes(taskId)) {
      tasks.unshift(taskId); // Add to beginning for newest first
      localStorage.setItem(this.TASKS_KEY, JSON.stringify(tasks));
    }
  }

  static removeTask(taskId: string): void {
    const tasks = this.getStoredTasks();
    const filtered = tasks.filter(id => id !== taskId);
    localStorage.setItem(this.TASKS_KEY, JSON.stringify(filtered));
  }

  static getTaskCount(): number {
    return this.getStoredTasks().length;
  }

  static isSessionValid(): boolean {
    const sessionId = localStorage.getItem(this.SESSION_KEY);
    const created = this.getSessionCreatedAt();
    
    if (!sessionId || !created) {
      return false;
    }

    // Check if session is older than 7 days (optional cleanup)
    const sevenDaysAgo = new Date();
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
    
    return created > sevenDaysAgo;
  }

  static cleanupOldSessions(): void {
    if (!this.isSessionValid()) {
      this.clearSession();
    }
  }
}