// Context7 pattern: Global type definitions for browser APIs

// Enhanced global types for the application
declare global {
  interface Window {
    // Add necessary browser APIs here
    gtag?: (...args: any[]) => void;
    dataLayer?: any[];
  }
}

// Module declarations for assets
declare module '*.svg' {
  const content: string;
  export default content;
}

declare module '*.png' {
  const content: string;
  export default content;
}

declare module '*.jpg' {
  const content: string;
  export default content;
}

declare module '*.jpeg' {
  const content: string;
  export default content;
}

// CSS modules support
declare module '*.module.css' {
  const classes: { [key: string]: string };
  export default classes;
}

export {}; 