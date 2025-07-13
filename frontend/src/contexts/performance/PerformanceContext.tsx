/**
 * Performance Context for Context7
 * 
 * Provides optimized state management with performance monitoring,
 * memoization, and lazy loading capabilities.
 */

import React, { createContext, useContext, useReducer, useCallback, useMemo, useEffect, useRef } from 'react';

// Performance metrics interface
interface PerformanceMetrics {
  renderTime: number;
  updateTime: number;
  memoryUsage: number;
  componentCount: number;
  rerenderCount: number;
  lastUpdate: Date;
}

// Performance state interface
interface PerformanceState {
  metrics: PerformanceMetrics;
  isEnabled: boolean;
  threshold: number;
  warnings: string[];
  optimizations: {
    memoization: boolean;
    lazyLoading: boolean;
    virtualScrolling: boolean;
    debouncing: boolean;
  };
}

// Performance actions
type PerformanceAction = 
  | { type: 'UPDATE_METRICS'; payload: Partial<PerformanceMetrics> }
  | { type: 'TOGGLE_MONITORING'; payload: boolean }
  | { type: 'SET_THRESHOLD'; payload: number }
  | { type: 'ADD_WARNING'; payload: string }
  | { type: 'CLEAR_WARNINGS' }
  | { type: 'TOGGLE_OPTIMIZATION'; payload: { key: keyof PerformanceState['optimizations']; value: boolean } };

// Initial state
const initialState: PerformanceState = {
  metrics: {
    renderTime: 0,
    updateTime: 0,
    memoryUsage: 0,
    componentCount: 0,
    rerenderCount: 0,
    lastUpdate: new Date(),
  },
  isEnabled: process.env.NODE_ENV === 'development',
  threshold: 16, // 16ms for 60fps
  warnings: [],
  optimizations: {
    memoization: true,
    lazyLoading: true,
    virtualScrolling: false,
    debouncing: true,
  },
};

// Performance reducer
const performanceReducer = (state: PerformanceState, action: PerformanceAction): PerformanceState => {
  switch (action.type) {
    case 'UPDATE_METRICS':
      return {
        ...state,
        metrics: {
          ...state.metrics,
          ...action.payload,
          lastUpdate: new Date(),
        },
      };
    
    case 'TOGGLE_MONITORING':
      return {
        ...state,
        isEnabled: action.payload,
      };
    
    case 'SET_THRESHOLD':
      return {
        ...state,
        threshold: action.payload,
      };
    
    case 'ADD_WARNING':
      return {
        ...state,
        warnings: [...state.warnings, action.payload],
      };
    
    case 'CLEAR_WARNINGS':
      return {
        ...state,
        warnings: [],
      };
    
    case 'TOGGLE_OPTIMIZATION':
      return {
        ...state,
        optimizations: {
          ...state.optimizations,
          [action.payload.key]: action.payload.value,
        },
      };
    
    default:
      return state;
  }
};

// Performance context interface
interface PerformanceContextType {
  state: PerformanceState;
  actions: {
    updateMetrics: (metrics: Partial<PerformanceMetrics>) => void;
    toggleMonitoring: (enabled: boolean) => void;
    setThreshold: (threshold: number) => void;
    addWarning: (warning: string) => void;
    clearWarnings: () => void;
    toggleOptimization: (key: keyof PerformanceState['optimizations'], value: boolean) => void;
    measureRenderTime: <T>(componentName: string, renderFn: () => T) => T;
    measureUpdateTime: <T>(updateFn: () => T) => T;
    checkMemoryUsage: () => void;
  };
  hooks: {
    usePerformanceMonitor: (componentName: string) => void;
    useMemoizedValue: <T>(value: T, deps: React.DependencyList) => T;
    useDebounced: <T>(value: T, delay: number) => T;
    useLazyComponent: <T>(importFn: () => Promise<{ default: React.ComponentType<T> }>) => React.ComponentType<T> | null;
  };
}

// Create context
const PerformanceContext = createContext<PerformanceContextType | undefined>(undefined);

// Performance provider component
export const PerformanceProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(performanceReducer, initialState);
  const componentCountRef = useRef(0);
  const rerenderCountRef = useRef(0);

  // Actions
  const updateMetrics = useCallback((metrics: Partial<PerformanceMetrics>) => {
    dispatch({ type: 'UPDATE_METRICS', payload: metrics });
  }, []);

  const toggleMonitoring = useCallback((enabled: boolean) => {
    dispatch({ type: 'TOGGLE_MONITORING', payload: enabled });
  }, []);

  const setThreshold = useCallback((threshold: number) => {
    dispatch({ type: 'SET_THRESHOLD', payload: threshold });
  }, []);

  const addWarning = useCallback((warning: string) => {
    dispatch({ type: 'ADD_WARNING', payload: warning });
  }, []);

  const clearWarnings = useCallback(() => {
    dispatch({ type: 'CLEAR_WARNINGS' });
  }, []);

  const toggleOptimization = useCallback((key: keyof PerformanceState['optimizations'], value: boolean) => {
    dispatch({ type: 'TOGGLE_OPTIMIZATION', payload: { key, value } });
  }, []);

  // Measure render time
  const measureRenderTime = useCallback(<T,>(componentName: string, renderFn: () => T): T => {
    if (!state.isEnabled) return renderFn();

    const start = performance.now();
    const result = renderFn();
    const end = performance.now();
    const renderTime = end - start;

    updateMetrics({ renderTime });

    if (renderTime > state.threshold) {
      addWarning(`Slow render detected in ${componentName}: ${renderTime.toFixed(2)}ms`);
    }

    return result;
  }, [state.isEnabled, state.threshold, updateMetrics, addWarning]);

  // Measure update time
  const measureUpdateTime = useCallback(<T,>(updateFn: () => T): T => {
    if (!state.isEnabled) return updateFn();

    const start = performance.now();
    const result = updateFn();
    const end = performance.now();
    const updateTime = end - start;

    updateMetrics({ updateTime });

    return result;
  }, [state.isEnabled, updateMetrics]);

  // Check memory usage
  const checkMemoryUsage = useCallback(() => {
    if (!state.isEnabled || !('memory' in performance)) return;

    const memoryInfo = (performance as any).memory;
    const memoryUsage = memoryInfo.usedJSHeapSize / memoryInfo.totalJSHeapSize;

    updateMetrics({ memoryUsage });

    if (memoryUsage > 0.8) {
      addWarning(`High memory usage detected: ${(memoryUsage * 100).toFixed(1)}%`);
    }
  }, [state.isEnabled, updateMetrics, addWarning]);

  // Performance monitoring hook
  const usePerformanceMonitor = useCallback((componentName: string) => {
    const renderCountRef = useRef(0);

    useEffect(() => {
      if (!state.isEnabled) return;

      renderCountRef.current++;
      componentCountRef.current++;
      rerenderCountRef.current++;

      updateMetrics({
        componentCount: componentCountRef.current,
        rerenderCount: rerenderCountRef.current,
      });

      // Check for excessive rerenders
      if (renderCountRef.current > 10) {
        addWarning(`Excessive rerenders detected in ${componentName}: ${renderCountRef.current}`);
      }
    });

    useEffect(() => {
      return () => {
        if (state.isEnabled) {
          componentCountRef.current = Math.max(0, componentCountRef.current - 1);
        }
      };
    }, []);
  }, [state.isEnabled, updateMetrics, addWarning]);

  // Memoized value hook
  const useMemoizedValue = useCallback(<T,>(value: T, deps: React.DependencyList): T => {
    if (!state.optimizations.memoization) return value;
    
    return useMemo(() => value, deps);
  }, [state.optimizations.memoization]);

  // Debounced value hook
  const useDebounced = useCallback(<T,>(value: T, delay: number): T => {
    const [debouncedValue, setDebouncedValue] = React.useState(value);

    useEffect(() => {
      if (!state.optimizations.debouncing) {
        setDebouncedValue(value);
        return;
      }

      const handler = setTimeout(() => {
        setDebouncedValue(value);
      }, delay);

      return () => {
        clearTimeout(handler);
      };
    }, [value, delay, state.optimizations.debouncing]);

    return debouncedValue;
  }, [state.optimizations.debouncing]);

  // Lazy component hook
  const useLazyComponent = useCallback(<T,>(
    importFn: () => Promise<{ default: React.ComponentType<T> }>
  ): React.ComponentType<T> | null => {
    const [component, setComponent] = React.useState<React.ComponentType<T> | null>(null);

    useEffect(() => {
      if (!state.optimizations.lazyLoading) return;

      let isMounted = true;

      importFn().then(({ default: Component }) => {
        if (isMounted) {
          setComponent(() => Component);
        }
      }).catch(error => {
        if (isMounted) {
          addWarning(`Failed to load lazy component: ${error.message}`);
        }
      });

      return () => {
        isMounted = false;
      };
    }, [importFn, state.optimizations.lazyLoading]);

    return component;
  }, [state.optimizations.lazyLoading, addWarning]);

  // Memory usage monitoring
  useEffect(() => {
    if (!state.isEnabled) return;

    const interval = setInterval(checkMemoryUsage, 5000);
    return () => clearInterval(interval);
  }, [state.isEnabled, checkMemoryUsage]);

  // Context value
  const contextValue = useMemo(
    () => ({
      state,
      actions: {
        updateMetrics,
        toggleMonitoring,
        setThreshold,
        addWarning,
        clearWarnings,
        toggleOptimization,
        measureRenderTime,
        measureUpdateTime,
        checkMemoryUsage,
      },
      hooks: {
        usePerformanceMonitor,
        useMemoizedValue,
        useDebounced,
        useLazyComponent,
      },
    }),
    [
      state,
      updateMetrics,
      toggleMonitoring,
      setThreshold,
      addWarning,
      clearWarnings,
      toggleOptimization,
      measureRenderTime,
      measureUpdateTime,
      checkMemoryUsage,
      usePerformanceMonitor,
      useMemoizedValue,
      useDebounced,
      useLazyComponent,
    ]
  );

  return (
    <PerformanceContext.Provider value={contextValue}>
      {children}
    </PerformanceContext.Provider>
  );
};

// Hook to use performance context
export const usePerformance = (): PerformanceContextType => {
  const context = useContext(PerformanceContext);
  if (!context) {
    throw new Error('usePerformance must be used within a PerformanceProvider');
  }
  return context;
};

// HOC for performance monitoring
export const withPerformanceMonitoring = <P extends object>(
  Component: React.ComponentType<P>,
  componentName?: string
) => {
  const WrappedComponent = React.memo((props: P) => {
    const { hooks } = usePerformance();
    
    hooks.usePerformanceMonitor(componentName || Component.name || 'Anonymous');
    
    return <Component {...props} />;
  });

  WrappedComponent.displayName = `withPerformanceMonitoring(${Component.displayName || Component.name || 'Component'})`;

  return WrappedComponent;
};

// Performance optimization utilities
export const PerformanceUtils = {
  // Memoize expensive computations
  memoize: <T extends (...args: any[]) => any>(fn: T): T => {
    const cache = new Map();
    
    return ((...args: Parameters<T>) => {
      const key = JSON.stringify(args);
      
      if (cache.has(key)) {
        return cache.get(key);
      }
      
      const result = fn(...args);
      cache.set(key, result);
      
      return result;
    }) as T;
  },

  // Debounce function calls
  debounce: <T extends (...args: any[]) => any>(fn: T, delay: number): T => {
    let timeoutId: NodeJS.Timeout;
    
    return ((...args: Parameters<T>) => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => fn(...args), delay);
    }) as T;
  },

  // Throttle function calls
  throttle: <T extends (...args: any[]) => any>(fn: T, delay: number): T => {
    let lastCall = 0;
    
    return ((...args: Parameters<T>) => {
      const now = Date.now();
      
      if (now - lastCall >= delay) {
        lastCall = now;
        return fn(...args);
      }
    }) as T;
  },

  // Virtual scrolling helper
  createVirtualList: (items: any[], itemHeight: number, containerHeight: number) => {
    const visibleCount = Math.ceil(containerHeight / itemHeight);
    const buffer = Math.floor(visibleCount / 2);
    
    return (scrollTop: number) => {
      const startIndex = Math.floor(scrollTop / itemHeight);
      const endIndex = Math.min(startIndex + visibleCount + buffer, items.length);
      const visibleItems = items.slice(Math.max(0, startIndex - buffer), endIndex);
      
      return {
        visibleItems,
        startIndex: Math.max(0, startIndex - buffer),
        endIndex,
        totalHeight: items.length * itemHeight,
        offsetY: Math.max(0, startIndex - buffer) * itemHeight,
      };
    };
  },
};

export default PerformanceContext; 