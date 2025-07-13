// Context7 pattern: Global type definitions for browser APIs and MUI compatibility

// Enhanced window interface with additional browser APIs
declare global {
  interface Window {
    // Add other necessary browser APIs here
    gtag?: (...args: any[]) => void;
    dataLayer?: any[];
  }
}

// MUI theme augmentation for TypeScript support
declare module '@mui/material/styles' {
  interface Palette {
    gradient: {
      primary: string;
      secondary: string;
    };
  }
  
  interface PaletteOptions {
    gradient?: {
      primary?: string;
      secondary?: string;
    };
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

declare module '*.gif' {
  const content: string;
  export default content;
}

declare module '*.webp' {
  const content: string;
  export default content;
}

// CSS modules support
declare module '*.module.css' {
  const classes: { [key: string]: string };
  export default classes;
}

declare module '*.module.scss' {
  const classes: { [key: string]: string };
  export default classes;
}

export {}; 