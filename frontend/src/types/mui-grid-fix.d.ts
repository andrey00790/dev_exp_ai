// Context7 pattern: Global type definitions for MUI Grid compatibility

declare module '@mui/material/Grid' {
  interface GridProps {
    item?: boolean;
    container?: boolean;
    xs?: boolean | number;
    sm?: boolean | number;
    md?: boolean | number;
    lg?: boolean | number;
    xl?: boolean | number;
    spacing?: number;
  }
}

// Extend global types for better compatibility
declare global {
  namespace JSX {
    interface IntrinsicElements {
      // Allow Grid with item prop for backwards compatibility
    }
  }
}

export {}; 